import apiClient from './apiClient';

const login = (email, password) => {
  const formData = new URLSearchParams();
  formData.append('username', email); // FastAPI's OAuth2PasswordRequestForm expects 'username'
  formData.append('password', password);
  return apiClient.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
};

const getCurrentUser = () => {
  return apiClient.get('/auth/me');
};

export default {
  login,
  getCurrentUser,
};
