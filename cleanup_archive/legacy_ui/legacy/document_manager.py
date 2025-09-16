import os
from datetime import datetime
import uuid

class DocumentManager:
    def __init__(self):
        self.documents = {}
        self.version_history = {}

    def add_document(self, filename, file_path):
        doc_id = str(uuid.uuid4())
        self.documents[doc_id] = {
            "filename": filename,
            "path": file_path,
            "created_at": datetime.now(),
            "versions": []
        }
        self._add_version(doc_id, file_path)
    
    def get_document(self, doc_id):
        return self.documents.get(doc_id, None)
    
    def get_document_content(self, doc_id):
        document = self.get_document(doc_id)
        if document:
            with open(document['path'], 'r', encoding='utf-8') as file:
                return file.read()
        return None

    def _add_version(self, doc_id, file_path):
        version_id = str(uuid.uuid4())
        version_entry = {
            "version_id": version_id,
            "file_path": file_path,
            "timestamp": datetime.now()
        }
        self.version_history.setdefault(doc_id, []).append(version_entry)
    
    def revert_document(self, doc_id, version_id):
        if doc_id in self.version_history:
            versions = self.version_history[doc_id]
            for version in versions:
                if version["version_id"] == version_id:
                    self.documents[doc_id]["path"] = version["file_path"]
                    return "Document reverted to version {}".format(version_id)
        return "Version not found."