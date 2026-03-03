import json
import os
import uuid
from datetime import datetime, timezone
from io import BytesIO, StringIO
import csv
import re

import joblib
import numpy as np
import pandas as pd


_MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024
_MAX_CONTEXT_CHARS = 12000
_MODEL_FEATURES = ["ApplicantIncome", "CoapplicantIncome", "LoanAmount", "Credit_History"]
_FEATURE_ALIASES = {
    "ApplicantIncome": ["applicantincome", "applicant_income", "income"],
    "CoapplicantIncome": ["coapplicantincome", "coapplicant_income"],
    "LoanAmount": ["loanamount", "loan_amount"],
    "Credit_History": ["credit_history", "credithistory"],
}
_SESSIONS = {}


_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
_ML_MODEL_PATH = os.path.join(_BASE_DIR, "ml_models", "model.pkl")


def _load_local_model():
    try:
        return joblib.load(_ML_MODEL_PATH)
    except Exception:
        return None


_LOCAL_MODEL = _load_local_model()


def _normalize_column(name):
    return str(name).strip().lower().replace(" ", "_")


def _trim_text(value, limit=_MAX_CONTEXT_CHARS):
    value = (value or "").strip()
    return value[:limit]


def _find_column(df, aliases):
    normalized = {_normalize_column(c): c for c in df.columns}
    for alias in aliases:
        candidate = normalized.get(_normalize_column(alias))
        if candidate is not None:
            return candidate
    return None


def _to_numeric_series(series):
    if series is None:
        return None
    cleaned = series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def _as_percent(numerator, denominator):
    if not denominator:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 2)


def _normalize_dataframe(df):
    if df is None or df.empty:
        raise ValueError("Uploaded file has no usable rows.")
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    if df.empty:
        raise ValueError("Uploaded file contains only empty rows/columns.")
    df.columns = [str(col).strip() or f"column_{idx+1}" for idx, col in enumerate(df.columns)]
    return df


def _decode_text_with_fallback(file_bytes):
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return file_bytes.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace"), "utf-8-replace"


def _read_csv_flexible(file_bytes):
    text, _encoding = _decode_text_with_fallback(file_bytes)
    sample = text[:4096]

    delimiters = [",", ";", "\t", "|"]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(delimiters))
        delimiters = [dialect.delimiter] + [d for d in delimiters if d != dialect.delimiter]
    except Exception:
        pass

    last_error = None
    for sep in delimiters:
        try:
            df = pd.read_csv(
                StringIO(text),
                sep=sep,
                engine="python",
                on_bad_lines="skip",
            )
            if not df.empty and df.shape[1] >= 1:
                return _normalize_dataframe(df)
        except Exception as exc:
            last_error = exc

    try:
        df = pd.read_csv(
            StringIO(text),
            sep=None,
            engine="python",
            on_bad_lines="skip",
        )
        return _normalize_dataframe(df)
    except Exception as exc:
        last_error = exc

    raise ValueError(f"Could not parse CSV file. {last_error}")


def _parse_upload_to_dataframe(file_name, file_bytes):
    upload_warning = None
    if not file_bytes:
        raise ValueError("Upload is empty.")
    if len(file_bytes) > _MAX_UPLOAD_BYTES:
        limit_mb = max(1, _MAX_UPLOAD_BYTES // (1024 * 1024))
        upload_warning = (
            f"Upload exceeded {limit_mb}MB. Only the first {limit_mb}MB was analyzed."
        )
        file_bytes = file_bytes[:_MAX_UPLOAD_BYTES]

    ext = os.path.splitext(file_name or "")[1].lower()
    if ext == ".csv":
        return _read_csv_flexible(file_bytes), upload_warning
    if ext in {".json"}:
        return _normalize_dataframe(pd.read_json(BytesIO(file_bytes))), upload_warning
    if ext in {".txt", ".tsv"}:
        return _read_csv_flexible(file_bytes), upload_warning
    if ext in {".xlsx", ".xls"}:
        try:
            return _normalize_dataframe(pd.read_excel(BytesIO(file_bytes))), upload_warning
        except Exception as exc:
            raise ValueError(f"Could not parse spreadsheet file: {exc}") from exc

    return _read_csv_flexible(file_bytes), upload_warning


def _extract_model_features(df):
    normalized = {_normalize_column(c): c for c in df.columns}
    mapped = {}

    for canonical, aliases in _FEATURE_ALIASES.items():
        source_column = None
        for alias in aliases:
            if alias in normalized:
                source_column = normalized[alias]
                break
        if source_column is not None:
            mapped[canonical] = source_column

    if not all(feature in mapped for feature in _MODEL_FEATURES):
        return None

    extracted = pd.DataFrame()
    for feature in _MODEL_FEATURES:
        extracted[feature] = pd.to_numeric(df[mapped[feature]], errors="coerce").fillna(0.0)
    return extracted


def _build_dataset_summary(df):
    row_count = int(len(df))
    columns = [str(c) for c in df.columns][:40]

    numeric_df = df.select_dtypes(include=["number"]).copy()
    numeric_summary = {}
    if not numeric_df.empty:
        desc = numeric_df.describe().transpose().head(12)
        for index, row in desc.iterrows():
            numeric_summary[str(index)] = {
                "mean": round(float(row.get("mean", 0.0)), 4),
                "min": round(float(row.get("min", 0.0)), 4),
                "max": round(float(row.get("max", 0.0)), 4),
            }

    return {
        "rows": row_count,
        "columns": columns,
        "numeric_summary": numeric_summary,
        "preview_rows": df.head(5).fillna("").to_dict(orient="records"),
    }


def _build_portfolio_insights(df):
    row_count = len(df)
    insights = {
        "audience": "lender_portfolio" if row_count > 1 else "individual_borrower",
        "row_count": int(row_count),
        "column_count": int(df.shape[1]),
    }

    missing_pct = ((df.isna().sum() / max(1, row_count)) * 100).round(2)
    top_missing = missing_pct[missing_pct > 0].sort_values(ascending=False).head(8)
    insights["missing_data_top"] = {str(k): float(v) for k, v in top_missing.items()}

    numeric_df = df.select_dtypes(include=["number"]).copy()
    numeric_profiles = {}
    for col in list(numeric_df.columns)[:12]:
        col_data = numeric_df[col].dropna()
        if col_data.empty:
            continue
        numeric_profiles[str(col)] = {
            "mean": round(float(col_data.mean()), 2),
            "median": round(float(col_data.median()), 2),
            "p25": round(float(col_data.quantile(0.25)), 2),
            "p75": round(float(col_data.quantile(0.75)), 2),
            "min": round(float(col_data.min()), 2),
            "max": round(float(col_data.max()), 2),
        }
    insights["numeric_profiles"] = numeric_profiles

    categorical_profiles = {}
    object_cols = [c for c in df.columns if df[c].dtype == "object"][:8]
    for col in object_cols:
        vc = (
            df[col]
            .astype(str)
            .str.strip()
            .replace({"": np.nan})
            .dropna()
            .value_counts(dropna=True)
            .head(5)
        )
        if vc.empty:
            continue
        categorical_profiles[str(col)] = [
            {"value": str(k), "count": int(v), "percent": _as_percent(v, row_count)}
            for k, v in vc.items()
        ]
    insights["categorical_profiles"] = categorical_profiles

    # Risk-tier scoring by common credit dataset signals.
    risk_score = pd.Series(np.zeros(row_count), index=df.index, dtype=float)

    credit_history_col = _find_column(df, ["credit_history", "credit_history_status"])
    if credit_history_col is not None:
        ch = df[credit_history_col]
        if pd.api.types.is_numeric_dtype(ch):
            risk_score += (pd.to_numeric(ch, errors="coerce").fillna(0) <= 0).astype(int) * 2
        else:
            ch_txt = ch.astype(str).str.lower()
            bad_patterns = r"(critical|delayed|arrears|poor|bad|none|no)"
            risk_score += ch_txt.str.contains(bad_patterns, regex=True, na=False).astype(int) * 2

    duration_col = _find_column(df, ["duration", "loan_duration", "loan_term"])
    if duration_col is not None:
        duration = _to_numeric_series(df[duration_col]).fillna(0)
        risk_score += (duration >= 36).astype(int)
        risk_score += (duration >= 60).astype(int)

    installment_col = _find_column(
        df, ["installment_rate", "installment_commitment", "installment"]
    )
    if installment_col is not None:
        inst = _to_numeric_series(df[installment_col]).fillna(0)
        risk_score += (inst >= inst.quantile(0.75)).astype(int)

    debtors_col = _find_column(df, ["other_debtors", "other_parties"])
    if debtors_col is not None:
        debtors_txt = df[debtors_col].astype(str).str.lower()
        risk_score += debtors_txt.str.contains(r"(co-applicant|guarantor|yes)", na=False).astype(int)

    amount_col = _find_column(df, ["loan_amount", "credit_amount", "amount"])
    if amount_col is not None:
        amount = _to_numeric_series(df[amount_col]).fillna(0)
        risk_score += (amount >= amount.quantile(0.75)).astype(int)

    # Segment portfolio.
    tiers = pd.cut(
        risk_score,
        bins=[-1, 1.5, 3.5, 99],
        labels=["low", "medium", "high"],
    )
    tier_counts = tiers.value_counts(dropna=False)
    risk_distribution = {
        str(k): {"count": int(v), "percent": _as_percent(v, row_count)}
        for k, v in tier_counts.items()
    }
    insights["risk_distribution"] = risk_distribution

    high_mask = tiers == "high"
    high_risk_share = _as_percent(high_mask.sum(), row_count)
    insights["high_risk_share_percent"] = high_risk_share

    # High-risk segmentation by purpose/employment/checking when available.
    segment_findings = []
    for alias_group in [
        ["purpose", "loan_purpose"],
        ["employment", "employment_length", "employment_since"],
        ["checking_status", "checking_account", "status_checking"],
        ["savings_status", "savings", "savings_account"],
    ]:
        seg_col = _find_column(df, alias_group)
        if seg_col is None:
            continue
        seg_df = pd.DataFrame({"segment": df[seg_col].astype(str), "is_high": high_mask.astype(int)})
        grp = seg_df.groupby("segment", dropna=False)["is_high"].agg(["count", "mean"]).reset_index()
        grp["high_risk_percent"] = (grp["mean"] * 100).round(2)
        grp = grp.sort_values(["high_risk_percent", "count"], ascending=[False, False]).head(3)
        for _, row in grp.iterrows():
            segment_findings.append(
                {
                    "column": str(seg_col),
                    "segment": str(row["segment"]),
                    "records": int(row["count"]),
                    "high_risk_percent": float(row["high_risk_percent"]),
                }
            )
    insights["high_risk_segments"] = segment_findings[:8]

    limitations = []
    if row_count < 30:
        limitations.append("Small sample size; stability of patterns is limited.")
    if not numeric_profiles:
        limitations.append("Limited numeric fields; quantitative inference is constrained.")
    target_col = _find_column(df, ["target", "label", "loan_status", "class", "risk"])
    if target_col is None:
        limitations.append("No observed outcome/target column detected; this is risk screening, not performance validation.")
    insights["limitations"] = limitations

    return insights


def _compute_local_model_insights(df):
    if _LOCAL_MODEL is None:
        return {"available": False, "message": "Local ML model could not be loaded."}

    extracted = _extract_model_features(df)
    if extracted is None:
        return {
            "available": False,
            "message": "Uploaded data does not contain the required model features.",
            "required_features": _MODEL_FEATURES,
        }

    predictions = _LOCAL_MODEL.predict(extracted)
    approved = int((predictions == 1).sum())
    rejected = int((predictions == 0).sum())
    total = int(len(predictions))
    approval_rate = round((approved / total) * 100, 2) if total else 0.0

    result = {
        "available": True,
        "records_scored": total,
        "approved_count": approved,
        "rejected_count": rejected,
        "approval_rate_percent": approval_rate,
    }

    if hasattr(_LOCAL_MODEL, "predict_proba"):
        probabilities = _LOCAL_MODEL.predict_proba(extracted)[:, 1]
        result["average_approval_probability"] = round(float(probabilities.mean()), 4)

    return result


def _fallback_guidance(summary, model_insights, notes, portfolio_insights=None):
    portfolio_insights = portfolio_insights or {}
    risk_dist = portfolio_insights.get("risk_distribution", {})
    high_info = risk_dist.get("high", {})
    med_info = risk_dist.get("medium", {})
    low_info = risk_dist.get("low", {})
    top_segments = portfolio_insights.get("high_risk_segments", [])

    bullets = [
        f"Uploaded dataset contains {summary.get('rows', 0)} rows and {len(summary.get('columns', []))} columns.",
        f"Primary columns detected: {', '.join(summary.get('columns', [])[:10])}.",
        f"Risk tier distribution: high={high_info.get('percent', 0)}%, medium={med_info.get('percent', 0)}%, low={low_info.get('percent', 0)}%.",
        "Prioritize underwriting review queue for the highest-risk tier before medium and low segments.",
        "Tighten approval thresholds where long duration and high installment burden co-occur.",
        "Apply stronger documentation requirements for segments showing elevated high-risk concentration.",
        "Use purpose-based and employment-based segmentation to calibrate policy rather than blanket rules.",
        "Track rejection/approval drift per high-risk segment monthly to detect policy mismatch early.",
        "Set exception-handling criteria for borderline medium-risk applicants to reduce false rejects.",
        "Recalculate risk tiers after policy changes and compare distribution shift before/after rollout.",
    ]
    if top_segments:
        top = top_segments[0]
        bullets.append(
            f"Highest-risk segment detected: {top.get('column')}={top.get('segment')} "
            f"with {top.get('high_risk_percent', 0)}% high-risk rate across {top.get('records', 0)} records."
        )
    if model_insights.get("available"):
        bullets.append(
            f"Local model snapshot: approval rate is {model_insights.get('approval_rate_percent', 0)}% "
            f"across {model_insights.get('records_scored', 0)} uploaded records."
        )
        bullets.append(
            f"Model estimates: approved={model_insights.get('approved_count', 0)}, "
            f"rejected={model_insights.get('rejected_count', 0)}."
        )
    if notes:
        bullets.append("Incorporate the provided notes into segment-specific policy adjustments.")

    while len(bullets) < 10:
        bullets.append("Document decision rationale per risk tier to improve auditability and model governance.")
    return "\n".join(f"- {item}" for item in bullets[:16])


def _enforce_minimum_bullets(
    guidance, summary, model_insights, notes, portfolio_insights=None, minimum=10
):
    text = (guidance or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullet_lines = [line for line in lines if line.startswith("- ") or line.startswith("* ")]

    if len(bullet_lines) >= minimum:
        return text

    extra = _fallback_guidance(summary, model_insights, notes, portfolio_insights=portfolio_insights)
    extra_lines = [line for line in extra.splitlines() if line.strip()]

    merged = lines[:] if lines else []
    if merged and not any("bullet" in line.lower() for line in merged[:2]):
        merged.insert(0, "Detailed Guidance (file-based):")

    existing = set(merged)
    for line in extra_lines:
        if line not in existing:
            merged.append(line)
            existing.add(line)
        current_bullets = [l for l in merged if l.startswith("- ") or l.startswith("* ")]
        if len(current_bullets) >= minimum:
            break

    return "\n".join(merged)


def _normalize_followup_length(answer, min_words=260, max_words=340):
    text = (answer or "").strip()
    if not text:
        return text

    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words])

    if len(words) < min_words:
        filler = (
            " Based on the uploaded portfolio, prioritize high-risk segment controls first, "
            "then recalibrate medium-risk thresholds, and keep low-risk approvals efficient. "
            "Track approval-rate drift, segment default proxies, and policy exceptions weekly. "
            "Document underwriting reasons with segment tags to improve governance and future model tuning."
        )
        expanded = text + filler
        return " ".join(expanded.split()[:max_words])

    return text


def _ensure_followup_bullets(answer, min_points=7):
    text = (answer or "").strip()
    if not text:
        return text

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets = [line for line in lines if line.startswith("- ") or line.startswith("* ")]
    has_topic = any(line.lower().startswith("main topic:") for line in lines)

    if not has_topic:
        lines.insert(0, "Main Topic: Portfolio risk follow-up strategy")

    if len(bullets) < min_points:
        extra_points = [
            "- Prioritize the highest-risk borrower segment for manual review before approval.",
            "- Tighten thresholds where long duration, high installment burden, and weak history overlap.",
            "- Separate policy rules by loan purpose and employment profile to reduce blanket decisions.",
            "- Track weekly approval-rate and rejection-rate shifts by risk tier for early drift detection.",
            "- Add exception governance: require documented rationale for overrides in medium/high risk.",
            "- Monitor concentration risk by segment and cap exposure where risk density is elevated.",
            "- Recompute risk tiers monthly and compare policy impact against prior cycle outcomes.",
            "- Improve data quality controls for fields with high missingness before next decision cycle.",
        ]
        existing = set(lines)
        for point in extra_points:
            if point not in existing:
                lines.append(point)
                existing.add(point)
            current_bullets = [l for l in lines if l.startswith("- ") or l.startswith("* ")]
            if len(current_bullets) >= min_points:
                break

    return "\n".join(lines)


def _google_chat(messages, max_tokens=900):
    api_key = (os.getenv("GOOGLE_API_KEY") or "").strip().strip('"')
    if not api_key:
        return None, "GOOGLE_API_KEY is not configured. Returning local fallback guidance."

    try:
        import google.generativeai as genai
    except Exception:
        return (
            None,
            "google-generativeai dependency is missing. Install requirements and retry.",
        )

    model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash").strip()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=model_name)

    # Flatten chat messages into a single prompt for Gemini.
    conversation = []
    for item in messages:
        role = str(item.get("role", "user")).upper()
        content = str(item.get("content", "")).strip()
        if content:
            conversation.append(f"{role}: {content}")
    prompt = "\n\n".join(conversation)

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.2, "max_output_tokens": max_tokens},
        )
        text = getattr(response, "text", None)
        if text:
            return text, None
        return None, "Google API returned an empty response."
    except Exception as exc:
        return None, f"Google API error: {exc}"


def analyze_financial_upload(file_name=None, file_bytes=None, notes=""):
    notes = _trim_text(notes)
    df, upload_warning = _parse_upload_to_dataframe(file_name or "upload.csv", file_bytes or b"")
    summary = _build_dataset_summary(df)
    model_insights = _compute_local_model_insights(df)
    portfolio_insights = _build_portfolio_insights(df)

    prompt_payload = {
        "dataset_summary": summary,
        "portfolio_insights": portfolio_insights,
        "model_insights": model_insights,
        "client_notes": notes,
    }

    system_prompt = (
        "You are a portfolio credit analyst AI. You must analyze the uploaded file context and produce accurate, "
        "decision-ready guidance grounded in the provided dataset summary, portfolio insights, and model insights. "
        "Return a detailed response with explicit sections and at least 10 bullet points total. "
        "Required sections: Key Findings, Risks, Action Plan (30/60/90 days), Monitoring Checklist, "
        "and Follow-up Questions. Use concise bullets with explicit numbers/percentages and segment-level findings. "
        "Do not give generic personal-finance filler. The audience is a lender/portfolio manager unless row_count=1."
    )
    user_prompt = (
        "Analyze this uploaded financial data and provide a detailed, accurate advisory response.\n"
        "Formatting rules:\n"
        "- Use markdown headings for required sections.\n"
        "- Use bullet points in every section.\n"
        "- Ensure at least 10 bullets across the full response.\n"
        "- Base every recommendation on the uploaded file data provided below.\n"
        "- Include portfolio segmentation and risk concentration observations.\n"
        "- Quantify findings using counts, percentages, medians, quartiles, or top categories.\n"
        "- Explicitly state data limitations and confidence bounds.\n\n"
        f"{json.dumps(prompt_payload, indent=2)}"
    )

    guidance, error = _google_chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        max_tokens=1400,
    )
    if not guidance:
        guidance = _fallback_guidance(
            summary, model_insights, notes, portfolio_insights=portfolio_insights
        )
    guidance = _enforce_minimum_bullets(
        guidance,
        summary,
        model_insights,
        notes,
        portfolio_insights=portfolio_insights,
        minimum=10,
    )

    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_summary": summary,
        "model_insights": model_insights,
        "notes": notes,
        "initial_guidance": guidance,
        "history": [],
    }

    return {
        "session_id": session_id,
        "guidance": guidance,
        "dataset_summary": summary,
        "portfolio_insights": portfolio_insights,
        "model_insights": model_insights,
        "provider_warning": " | ".join([item for item in [upload_warning, error] if item]) or None,
    }


def continue_advisor_chat(session_id, question):
    session = _SESSIONS.get(session_id)
    if not session:
        raise ValueError("Session not found. Start a new analysis session first.")

    question = _trim_text(question, limit=3000)
    if not question:
        raise ValueError("Question is required.")

    history = session["history"][-8:]
    messages = [
        {
            "role": "system",
            "content": (
                "You are continuing a financial advisory session. Keep answers clear and factual. "
                "Reference the prior guidance and data context, and provide concise, actionable next steps. "
                "The response should be around 300 words (target 280-320 words). "
                "Format must include 'Main Topic:' on the first line and at least 7 bullet points."
            ),
        },
        {
            "role": "user",
            "content": (
                "Session context:\n"
                f"Dataset summary: {json.dumps(session['dataset_summary'])}\n"
                f"Portfolio insights: {json.dumps(session.get('portfolio_insights', {}))}\n"
                f"Model insights: {json.dumps(session['model_insights'])}\n"
                f"Initial guidance: {session['initial_guidance']}"
            ),
        },
    ]

    for item in history:
        messages.append({"role": "user", "content": item["question"]})
        messages.append({"role": "assistant", "content": item["answer"]})
    messages.append({"role": "user", "content": question})

    answer, error = _google_chat(messages, max_tokens=700)
    if not answer:
        answer = (
            "I could not reach the AI provider right now. Based on your uploaded data, "
            "focus on liquidity protection, debt reduction, and monthly budget variance tracking."
        )
    answer = _normalize_followup_length(answer)
    answer = _ensure_followup_bullets(answer, min_points=7)

    session["history"].append({"question": question, "answer": answer})
    return {"answer": answer, "provider_warning": error}

