from nodes.db_load import db_load

def retriever(db, debug=False):
    # retriever
    retriever = db.as_retriever()
        
    if debug:
        # cv load
        cv_path = './data/CV/ml_engineer_CV_3.txt'
        with open (cv_path, "r") as file:
            cv = file.read()

        retrieval_results = retriever.invoke(cv)
        return retrieval_results
    else:
        return retriever