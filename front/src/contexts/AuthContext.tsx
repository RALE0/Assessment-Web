import React, { createContext, useContext, useEffect, useState } from 'react';

export interface User {
  id: string;
  username: string;
  email?: string;
  lastLoginAt: string;
  sessionStartedAt: string;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  signup: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  // Helper function to parse JWT token
  const parseJwt = (token: string): any => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Error parsing JWT:', error);
      return null;
    }
  };

  useEffect(() => {
    // Check for existing session on app load
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    try {
      const token = localStorage.getItem('authToken');
      if (token) {
        // Parse JWT to get user info
        const tokenData = parseJwt(token);
        console.log('JWT Token data:', tokenData);
        
        // Validate token with backend
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://10.49.12.46:420/api'}/auth/verify`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          referrerPolicy: "unsafe-url"
        });

        if (response.ok) {
          const userData = await response.json();
          console.log('Verified user data:', userData);
          
          // Ensure user ID is properly set from token or response
          const user = userData.user;
          if (!user.id && tokenData) {
            user.id = tokenData.user_id || tokenData.sub || tokenData.id;
          }
          
          setUser(user);
        } else {
          localStorage.removeItem('authToken');
        }
      }
    } catch (error) {
      console.error('Session check failed:', error);
      localStorage.removeItem('authToken');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (username: string, password: string): Promise<void> => {
    try {
      setIsLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://10.49.12.46:420/api'}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
        credentials: 'include',
        referrerPolicy: "unsafe-url"
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      const data = await response.json();
      console.log('Login response:', data);
      
      // Store token and user data
      localStorage.setItem('authToken', data.token);
      
      // Parse JWT to ensure we have the correct user ID
      const tokenData = parseJwt(data.token);
      const user = data.user;
      if (!user.id && tokenData) {
        user.id = tokenData.user_id || tokenData.sub || tokenData.id;
      }
      
      setUser(user);

      // Log session start
      await logSessionActivity('login', user.id);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('authToken');
      
      if (user && token) {
        // Log session end
        await logSessionActivity('logout', user.id);
        
        // Notify backend of logout
        await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://10.49.12.46:420/api'}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          referrerPolicy: "unsafe-url"
        });
      }

      // Clear local storage and state
      localStorage.removeItem('authToken');
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
      // Clear state anyway
      localStorage.removeItem('authToken');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (username: string, email: string, password: string): Promise<void> => {
    try {
      setIsLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://10.49.12.46:420/api'}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
        referrerPolicy: "unsafe-url"
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Sign up failed');
      }

      const data = await response.json();
      console.log('Signup response:', data);
      
      // Store token and user data
      localStorage.setItem('authToken', data.token);
      
      // Parse JWT to ensure we have the correct user ID
      const tokenData = parseJwt(data.token);
      const user = data.user;
      if (!user.id && tokenData) {
        user.id = tokenData.user_id || tokenData.sub || tokenData.id;
      }
      
      setUser(user);

      // Log signup activity
      await logSessionActivity('login', user.id);
    } finally {
      setIsLoading(false);
    }
  };

  const resetPassword = async (email: string): Promise<void> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://10.49.12.46:420/api'}/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
      referrerPolicy: "unsafe-url"
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Password reset failed');
    }
  };

  const logSessionActivity = async (activity: string, userId: string): Promise<void> => {
    try {
      await fetch(`${import.meta.env.VITE_API_BASE_URL || 'https://10.49.12.46:420/api'}/auth/log-activity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({
          userId,
          activity,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          ipAddress: 'client-side' // Will be determined on backend
        }),
        referrerPolicy: "unsafe-url"
      });
    } catch (error) {
      console.error('Failed to log session activity:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    signup,
    logout,
    resetPassword,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};