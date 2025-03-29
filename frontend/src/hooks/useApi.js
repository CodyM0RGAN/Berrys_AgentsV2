import { useCallback, useState } from 'react';

/**
 * Custom hook for making API calls with loading and error states
 * 
 * @param {function} apiMethod - The API method to call from apiService
 * @returns {object} - An object containing the loading state, error, data, and execute function
 */
const useApi = (apiMethod) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [data, setData] = useState(null);

    /**
     * Execute the API call
     * 
     * @param {any} params - Parameters to pass to the API method
     * @returns {Promise} - A promise that resolves with the API response data
     */
    const execute = useCallback(async (...params) => {
        try {
            setLoading(true);
            setError(null);

            const response = await apiMethod(...params);
            setData(response.data);
            return response.data;
        } catch (err) {
            const errorMessage = err.response?.data?.message || err.message || 'An error occurred';
            setError(errorMessage);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [apiMethod]);

    return {
        loading,
        error,
        data,
        execute,
    };
};

export default useApi;
