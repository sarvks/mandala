import { Heart } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

export default function FavouriteButton({ templeId, size = "md", className = "" }) {
  const { user, favourites, toggleFavourite } = useAuth();
  const navigate = useNavigate();
  const isFav = favourites?.includes(templeId);

  const onClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      toast.info("Login to save favourite temples");
      navigate("/login");
      return;
    }
    try {
      const nowFav = await toggleFavourite(templeId);
      toast.success(nowFav ? "Saved to your temples" : "Removed from favourites");
    } catch {
      toast.error("Could not update favourite");
    }
  };

  const s = size === "sm" ? "h-8 w-8" : "h-10 w-10";
  const ic = size === "sm" ? "h-4 w-4" : "h-5 w-5";

  return (
    <button
      onClick={onClick}
      data-testid={`favourite-btn-${templeId}`}
      aria-label={isFav ? "Unfavourite" : "Favourite"}
      className={`${s} inline-flex items-center justify-center rounded-full border transition ${
        isFav
          ? "border-[#7C191E] bg-[#7C191E] text-white"
          : "border-stone-300 bg-white/90 text-[#475569] backdrop-blur hover:border-[#7C191E] hover:text-[#7C191E]"
      } ${className}`}
    >
      <Heart className={ic} strokeWidth={1.6} fill={isFav ? "currentColor" : "none"} />
    </button>
  );
}
