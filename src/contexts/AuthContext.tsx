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

  useEffect(() => {
    // Check for existing session on app load
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    try {
      const token = localStorage.getItem('authToken');
      if (token) {
        // Validate token with backend
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://172.28.69.96:8443'}/auth/verify`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData.user);
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
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://172.28.69.96:8443'}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      const data = await response.json();
      
      // Store token and user data
      localStorage.setItem('authToken', data.token);
      setUser(data.user);

      // Log session start
      await logSessionActivity('login', data.user.id);
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
        await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://172.28.69.96:8443'}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
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
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://172.28.69.96:8443'}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Sign up failed');
      }

      const data = await response.json();
      
      // Store token and user data
      localStorage.setItem('authToken', data.token);
      setUser(data.user);

      // Log signup activity
      await logSessionActivity('login', data.user.id);
    } finally {
      setIsLoading(false);
    }
  };

  const resetPassword = async (email: string): Promise<void> => {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://172.28.69.96:8443'}/auth/reset-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Password reset failed');
    }
  };

  const logSessionActivity = async (activity: string, userId: string): Promise<void> => {
    try {
      await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://172.28.69.96:8443'}/auth/log-activity`, {
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