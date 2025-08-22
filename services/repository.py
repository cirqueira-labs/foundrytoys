from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass(frozen=True)
class VectorStoreInfo:
    id: str
    name: str


@dataclass(frozen=True)
class FileInfo:
    id: str
    filename: str
    bytes: int | None = None


class ProjectsRepository(Protocol):
    def list_vector_stores(self) -> Iterable[VectorStoreInfo]: ...

    def list_vector_store_files(self, vector_store_id: str) -> Iterable[FileInfo]: ...

    def upload_file_to_vector_store(
        self, vector_store_id: str, file_path: str
    ) -> None: ...


class AzureProjectsRepository:
    def __init__(self, project_client) -> None:
        self.client = project_client

    def list_vector_stores(self) -> Iterable[VectorStoreInfo]:
        stores = self.client.agents.vector_stores.list()
        for vs in stores:
            yield VectorStoreInfo(id=vs.id, name=getattr(vs, "name", vs.id))

    def list_vector_store_files(self, vector_store_id: str) -> Iterable[FileInfo]:
        assocs = self.client.agents.vector_store_files.list(
            vector_store_id=vector_store_id
        )
        for assoc in assocs:
            try:
                f = self.client.agents.files.get(file_id=assoc.id)
                yield FileInfo(
                    id=f.id, filename=f.filename, bytes=getattr(f, "bytes", None)
                )
            except Exception:  # noqa: BLE001
                continue

    def upload_file_to_vector_store(self, vector_store_id: str, file_path: str) -> None:
        try:
            from azure.ai.agents.models import FilePurpose
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                "Dependência azure-ai-agents ausente. Adicione o pacote."
            ) from e
        uploaded = self.client.agents.files.upload_and_poll(
            file_path=file_path, purpose=FilePurpose.AGENTS
        )
        self.client.agents.vector_store_files.create_and_poll(
            vector_store_id=vector_store_id, file_id=uploaded.id
        )
