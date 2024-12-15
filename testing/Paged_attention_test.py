import numpy as np
import time
import tracemalloc

# Standard attention mechanism implementation
def standard_attention(Q, K, V):
    """
    Computes the standard attention mechanism.

    Args:
        Q (numpy.ndarray): Query matrix of shape (seq_len, d_k).
        K (numpy.ndarray): Key matrix of shape (seq_len, d_k).
        V (numpy.ndarray): Value matrix of shape (seq_len, d_v).

    Returns:
        numpy.ndarray: Output matrix of shape (seq_len, d_v) representing the attended values.
    """
    # d_k is the dimensionality of the keys and queries
    d_k = Q.shape[1] 
    # Calculate attention scores by dot product of Q and K transposed, scaled by 1/sqrt(d_k)
    scores = np.dot(Q, K.T) / np.sqrt(d_k)
    # Apply softmax to the scores to get attention weights
    attention_weights = softmax(scores)
    # Multiply attention weights by the value matrix V to get the output
    output = np.dot(attention_weights, V) 
    return output

# Paged attention mechanism implementation
def paged_attention(Q, K, V, block_size):
    """
    Computes the paged attention mechanism to reduce memory usage for long sequences.

    Args:
        Q (numpy.ndarray): Query matrix of shape (seq_len, d_k).
        K (numpy.ndarray): Key matrix of shape (seq_len, d_k).
        V (numpy.ndarray): Value matrix of shape (seq_len, d_v).
        block_size (int): Size of the blocks for paged computation.

    Returns:
        numpy.ndarray: Output matrix of shape (seq_len, d_v) representing the attended values.
    """
    # seq_len is the length of the input sequence, d_model is the dimensionality of the model
    seq_len, d_model = Q.shape 
    # Initialize output matrix with zeros
    output = np.zeros_like(Q) 
    # d_k is the dimensionality of the keys and queries
    d_k = d_model

    # Iterate over the sequence length with the specified block size
    for i in range(0, seq_len, block_size):
        # Extract a block of queries
        Q_block = Q[i:i+block_size] 
        # Extract the relevant keys and values up to the current block
        K_past = K[:i+block_size] 
        V_past = V[:i+block_size] 
        # Calculate attention scores for the current block
        scores = np.dot(Q_block, K_past.T) / np.sqrt(d_k) 
        # Apply softmax to the scores to get attention weights
        attention_weights = softmax(scores) 
        # Calculate the output for the current block
        output_block = np.dot(attention_weights, V_past) 
        # Place the output block in the correct position in the output matrix
        output[i:i+block_size] = output_block 
        # Delete intermediate variables to free up memory
        del scores, attention_weights 
    return output

# Softmax function implementation
def softmax(x):
    """
    Computes the softmax function for a given input array.

    Args:
        x (numpy.ndarray): Input array.

    Returns:
        numpy.ndarray: Array with softmax applied.
    """
    # Subtract the maximum value for numerical stability
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    # Return softmax values
    return e_x / np.sum(e_x, axis=-1, keepdims=True)

# Function to measure performance of a given function
def measure_performance(func, *args, **kwargs):
    """
    Measures the execution time and peak memory usage of a given function.

    Args:
        func (function): The function to be measured.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        tuple: A tuple containing the result of the function call, execution time, and peak memory usage.
    """
    # Start tracing memory allocation
    tracemalloc.start() 
    # Record the start time
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    exec_time = end_time - start_time
    peak_memory = peak / (1024**2)  
    return result, exec_time, peak_memory


if __name__ == "__main__":
    # Define the sequence length (number of tokens) and the model dimension (embedding size)
    seq_len = 1000  # Number of tokens in the input sequence
    d_model = 64    # Dimensionality of the embedding space

    # Generate random query, key, and value matrices for testing
    Q = np.random.rand(seq_len, d_model)
    K = np.random.rand(seq_len, d_model)
    V = np.random.rand(seq_len, d_model)

    # Measure performance for standard attention
    output_standard, standard_time, standard_memory = measure_performance(standard_attention, Q, K, V)
    print("Standard Attention:")
    print(f"Time taken: {standard_time:.4f} seconds")  # Print the execution time
    print(f"Peak memory usage: {standard_memory:.2f} MB")  # Print the peak memory usage

    # Define the block size for paged attention
    block_size = 500  # Number
    output_paged, paged_time, paged_memory = measure_performance(paged_attention, Q, K, V, block_size)
    print("\nPaged Attention:")
    print(f"Time taken: {paged_time:.4f} seconds")
    print(f"Peak memory usage: {paged_memory:.2f} MB")
