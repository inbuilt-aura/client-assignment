"use client";

import { useEffect, useState } from "react";
import { api, clearAccessToken, SignedInUser } from "@/lib/api";

export default function SessionControls() {
  const [user, setUser] = useState<SignedInUser | null>(null);

  useEffect(() => {
    api.currentUser().then(setUser).catch(() => setUser(null));
  }, []);

  function signOut() {
    clearAccessToken();
    window.location.assign("/login");
  }

  return <div className="account"><span className="avatar">{user?.email?.[0]?.toUpperCase() ?? "N"}</span><span>{user?.email ?? "Vendor account"}</span><button className="sign-out" type="button" onClick={signOut}>Sign out</button></div>;
}
