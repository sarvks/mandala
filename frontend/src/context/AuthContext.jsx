import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [favourites, setFavourites] = useState([]); // temple ids

  const refreshFavourites = useCallback(async () => {
    try {
      const { data } = await api.get("/favourites/me");
      setFavourites(data.temple_ids || []);
    } catch {
      setFavourites([]);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("mandala_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me")
      .then(async (r) => {
        setUser(r.data);
        await refreshFavourites();
      })
      .catch(() => {
        localStorage.removeItem("mandala_token");
      })
      .finally(() => setLoading(false));
  }, [refreshFavourites]);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("mandala_token", data.token);
    setUser(data.user);
    await refreshFavourites();
    return data.user;
  };

  const signup = async (name, email, password) => {
    const { data } = await api.post("/auth/signup", { name, email, password });
    localStorage.setItem("mandala_token", data.token);
    setUser(data.user);
    setFavourites([]);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem("mandala_token");
    setUser(null);
    setFavourites([]);
  };

  const toggleFavourite = async (templeId) => {
    if (!user) throw new Error("login required");
    const { data } = await api.post(`/favourites/${templeId}/toggle`);
    setFavourites(data.temple_ids || []);
    return data.favourited;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        favourites,
        login,
        signup,
        logout,
        toggleFavourite,
        refreshFavourites,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
