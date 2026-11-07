import { useRef, useState } from "react";
import { ChevronDown, Star, X } from "lucide-react";
import { Link } from "react-router-dom";
import { removeFavorite, useFavoriteWorkspaces } from "../favorites";

export function FavoriteMenu() {
  const [open, setOpen] = useState(false);
  const favorites = useFavoriteWorkspaces();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const close = () => { setOpen(false); triggerRef.current?.focus(); };

  return <div className="favorite-menu">
    <button ref={triggerRef} className="favorite-menu-trigger" type="button" aria-label={`즐겨찾기 메뉴 ${favorites.length}개`} aria-expanded={open} aria-controls="favorite-workspace-menu" onClick={() => setOpen((current) => !current)}>
      <Star aria-hidden="true" /><span>즐겨찾기</span><small>{favorites.length}</small><ChevronDown aria-hidden="true" />
    </button>
    {open && <section id="favorite-workspace-menu" className="favorite-menu-popover" aria-label="즐겨찾기 작업공간">
      <header><div><span className="eyebrow">FAVORITE WORKSPACES</span><h2>즐겨찾기</h2></div><button className="icon-button" type="button" aria-label="즐겨찾기 메뉴 닫기" onClick={close}><X aria-hidden="true" /></button></header>
      <p>홈에서 저장한 작업공간으로 바로 이동합니다. 이 목록은 현재 브라우저에만 저장됩니다.</p>
      {favorites.length === 0 ? <div className="favorite-menu-empty"><Star aria-hidden="true" /><strong>저장한 작업공간이 없습니다.</strong><span>홈의 DOE, SPC, FMEA 카드에서 즐겨찾기를 추가하세요.</span></div> : <ul className="favorite-menu-list">
        {favorites.map((favorite) => <li key={favorite.to}><Link to={favorite.to} onClick={() => setOpen(false)}>{favorite.title}</Link><button type="button" aria-label={`${favorite.title} 즐겨찾기 해제`} onClick={() => removeFavorite(favorite.to)}><X aria-hidden="true" /></button></li>)}
      </ul>}
    </section>}
  </div>;
}
