from pyramid.view import view_config

from finance_ai.services.ai_service import analyze_financial_upload, continue_advisor_chat


def _read_upload_payload(request):
    content_type = request.content_type
    if content_type is not None and "multipart/form-data" in str(content_type).lower():
        file_field = request.POST.get("file")
        notes_value = request.POST.get("notes")
        notes = (str(notes_value) if notes_value is not None else "").strip()
        if file_field is None or getattr(file_field, "file", None) is None:
            raise ValueError("A financial file upload is required.")
        file_name = file_field.filename or "upload.csv"
        file_bytes = file_field.file.read()
        return file_name, file_bytes, notes

    body = request.json_body or {}
    notes = (body.get("notes") or body.get("text") or "").strip()
    file_content = body.get("file_content")
    file_name = body.get("file_name", "upload.csv")
    if file_content is None or str(file_content).strip() == "":
        raise ValueError("Provide either multipart file upload or JSON file_content.")
    return file_name, str(file_content).encode("utf-8"), notes


@view_config(route_name="ai_analyze", renderer="json", request_method="POST")
@view_config(route_name="api_ai_analyze", renderer="json", request_method="POST")
def ai_analyze_view(request):
    try:
        file_name, file_bytes, notes = _read_upload_payload(request)
        result = analyze_financial_upload(file_name=file_name, file_bytes=file_bytes, notes=notes)
        return {"status": "success", **result}
    except ValueError as exc:
        request.response.status_code = 400
        return {"status": "error", "message": str(exc)}
    except Exception as exc:
        request.response.status_code = 500
        return {"status": "error", "message": str(exc)}


@view_config(route_name="ai_chat", renderer="json", request_method="POST")
@view_config(route_name="api_ai_chat", renderer="json", request_method="POST")
def ai_chat_view(request):
    try:
        body = request.json_body or {}
        session_id = (body.get("session_id") or "").strip()
        question = (body.get("question") or "").strip()
        if not session_id:
            raise ValueError("session_id is required.")
        result = continue_advisor_chat(session_id=session_id, question=question)
        return {"status": "success", **result}
    except ValueError as exc:
        request.response.status_code = 400
        return {"status": "error", "message": str(exc)}
    except Exception as exc:
        request.response.status_code = 500
        return {"status": "error", "message": str(exc)}
