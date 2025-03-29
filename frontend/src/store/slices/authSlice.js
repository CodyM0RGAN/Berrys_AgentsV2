import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';

// Mock login function - would be replaced with actual API call
const mockLogin = async (credentials) => {
    // Simulate API call
    return new Promise((resolve) => {
        setTimeout(() => {
            if (credentials.email === 'admin@example.com' && credentials.password === 'password') {
                resolve({
                    user: {
                        id: '1',
                        name: 'John Doe',
                        email: 'admin@example.com',
                        role: 'admin',
                    },
                    token: 'mock-jwt-token',
                });
            } else {
                throw new Error('Invalid credentials');
            }
        }, 1000);
    });
};

// Async thunks
export const login = createAsyncThunk(
    'auth/login',
    async (credentials, { rejectWithValue }) => {
        try {
            const response = await mockLogin(credentials);
            // Store token in localStorage
            localStorage.setItem('token', response.token);
            return response.user;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

export const logout = createAsyncThunk(
    'auth/logout',
    async () => {
        localStorage.removeItem('token');
        return null;
    }
);

// Check if user is already logged in
const token = localStorage.getItem('token');

const initialState = {
    user: null,
    token: token || null,
    isAuthenticated: !!token,
    loading: false,
    error: null,
};

const authSlice = createSlice({
    name: 'auth',
    initialState,
    reducers: {
        clearError: (state) => {
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        builder
            // Login
            .addCase(login.pending, (state) => {
                state.loading = true;
                state.error = null;
            })
            .addCase(login.fulfilled, (state, action) => {
                state.loading = false;
                state.user = action.payload;
                state.isAuthenticated = true;
                state.error = null;
            })
            .addCase(login.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })
            // Logout
            .addCase(logout.fulfilled, (state) => {
                state.user = null;
                state.token = null;
                state.isAuthenticated = false;
            });
    },
});

export const { clearError } = authSlice.actions;

export default authSlice.reducer;
