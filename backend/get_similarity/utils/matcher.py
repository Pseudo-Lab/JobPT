import numpy as np
import concurrent.futures
from typing import List, Dict, Any

# Numba가 설치되어 있지 않을 경우를 대비한 안전 장치
try:
    from numba import jit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    def jit(*args, **kwargs):
        def wrapper(func):
            return func
        return wrapper

class DenseMatcher:
    def __init__(self, num_workers: int = 4, **kwargs):
        # coverage 관련 파라미터 무시
        self.num_workers = num_workers

    # --------------------------------------------------------------------------
    # Numba Optimized Kernels (Static Methods)
    # --------------------------------------------------------------------------
    @staticmethod
    @jit(nopython=True, fastmath=True)
    def _fast_cosine_matrix(cv_vectors: np.ndarray, jd_vectors: np.ndarray) -> np.ndarray:
        """
        Calculates cosine similarity matrix between CV (N x D) and JD (M x D).
        """
        # N x M matrix
        dot_product = cv_vectors @ jd_vectors.T
        
        # Norm calculation
        cv_norms = np.empty(cv_vectors.shape[0], dtype=np.float32)
        for i in range(cv_vectors.shape[0]):
            s = 0.0
            for k in range(cv_vectors.shape[1]):
                val = cv_vectors[i, k]
                s += val * val
            cv_norms[i] = np.sqrt(s)
            
        jd_norms = np.empty(jd_vectors.shape[0], dtype=np.float32)
        for j in range(jd_vectors.shape[0]):
            s = 0.0
            for k in range(jd_vectors.shape[1]):
                val = jd_vectors[j, k]
                s += val * val
            jd_norms[j] = np.sqrt(s)
            
        # Divide by norms
        rows, cols = dot_product.shape
        for i in range(rows):
            for j in range(cols):
                denom = cv_norms[i] * jd_norms[j]
                if denom > 1e-9:
                    dot_product[i, j] /= denom
                else:
                    dot_product[i, j] = 0.0
                    
        return dot_product

    @staticmethod
    @jit(nopython=True, fastmath=True)
    def _calc_similarity_jit(sim_matrix: np.ndarray) -> float:
        """
        Returns average similarity only.
        """
        if sim_matrix.size == 0:
            return 0.0

        total_sim = 0.0
        count = 0
        rows, cols = sim_matrix.shape
        
        for i in range(rows):
            for j in range(cols):
                total_sim += sim_matrix[i, j]
                count += 1
        
        return total_sim / count if count > 0 else 0.0

    # --------------------------------------------------------------------------
    # Python helpers
    # --------------------------------------------------------------------------

    def _process_single_job(self, args):
        """
        Worker function for parallel processing.
        args: (job_id, jd_embs_list, cv_vec_np)
        """
        job_id, jd_embs, cv_vec_np = args
        
        if not jd_embs:
            return None
            
        # 모든 JD 청크 사용 (Coverage 필터링 없음)
        targets = jd_embs
        
        # Prepare JD Matrix (M x D)
        try:
            jd_vec_np = np.stack([np.array(j["values"], dtype=np.float32) for j in targets])
        except Exception:
            return None

        # 1. Compute Similarity Matrix
        sim_matrix = self._fast_cosine_matrix(cv_vec_np.astype(np.float32), jd_vec_np)
        
        # 2. Compute Average Similarity
        sim = self._calc_similarity_jit(sim_matrix)
        
        return {
            "job_id": job_id,
            "final_score": sim, # Similarity Only
            "similarity": sim
        }

    def compute_batch_parallel(self, cv_vecs_list: List[np.ndarray], job_embeddings_map: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if not cv_vecs_list or not job_embeddings_map:
            return []

        # Prepare CV Matrix (N x D)
        cv_vec_np = np.stack([np.array(v, dtype=np.float32) for v in cv_vecs_list])
        
        tasks = []
        for jid, jembs in job_embeddings_map.items():
            tasks.append((jid, jembs, cv_vec_np))
            
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(self._process_single_job, task) for task in tasks]
            for f in concurrent.futures.as_completed(futures):
                res = f.result()
                if res:
                    results.append(res)
                    
        return results
