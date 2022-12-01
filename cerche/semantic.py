from typing import *
import requests
from base import SearchABCRequestHandler
from autofaiss import build_index
from custom_logging import print
import torch
from sentence_transformers import SentenceTransformer

BATCH_EMBEDDING_SIZE = 512
class SemanticSearchRequestHandler(SearchABCRequestHandler):
    def search(
        self,
        q: str,
        n: int,
    ) -> Generator[str, None, None]:
        # TODO
        sentence_embeddings_model = None

        # https://www.sbert.net/docs/pretrained_models.html#model-overview
        sentence_embeddings_model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
        device = (
            "cuda:0" if torch.cuda.is_available() and self.server.use_gpu else "cpu"
        )

        print(f"Loaded sentence embedding model, device: {device}")

        sentence_embeddings_model = SentenceTransformer(
            sentence_embeddings_model_name, device=device
        )

        embeddings = []
        existing_conversation_starters_as_batch = [
            [
                e["content"]
                for e in self.server.[i : i + BATCH_EMBEDDING_SIZE]
            ]
            for i in range(
                0, len(existing_conversation_starters), BATCH_EMBEDDING_SIZE
            )
        ]
        for i, batch in enumerate(existing_conversation_starters_as_batch):
            emb = sentence_embeddings_model.encode(
                batch, show_progress_bar=False, device=device
            )

            # extends embeddings with batch
            embeddings.extend(emb)
            if logger:
                logger.info(
                    f"Computed embeddings - {len(batch)*(i+1)}/{len(existing_conversation_starters)}"
                )

        # flatten embeddings
        embeddings = np.array(embeddings)
        if logger:
            logger.info(f"Done, embeddings shape: {embeddings.shape}")

        # delete "embeddings" and "indexes" folders
        for folder in ["embeddings", "indexes"]:
            if os.path.exists(folder):
                shutil.rmtree(folder)

        if logger:
            logger.info("Saving embeddings to disk and building index to disk")
        os.makedirs("embeddings", exist_ok=True)
        np.save("embeddings/p1.npy", embeddings)
        index, _ = build_index(
            "embeddings",
            index_path="indexes/knn.index",
            max_index_memory_usage="6G",
            current_memory_available="7G",
        )
