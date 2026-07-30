
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests

@dataclass
class TradovateClient:
    username: str
    password: str
    app_id: str
    app_version: str
    cid: str
    sec: str
    device_id: str = ""
    demo: bool = True
    timeout: int = 12

    def __post_init__(self):
        self.base_url = "https://demo.tradovateapi.com/v1" if self.demo else "https://live.tradovateapi.com/v1"
        self.access_token = ""

    @property
    def configured(self) -> bool:
        return all([self.username, self.password, self.cid, self.sec])

    def authenticate(self) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("Tradovate credentials are incomplete.")
        payload = {
            "name": self.username,
            "password": self.password,
            "appId": self.app_id,
            "appVersion": self.app_version,
            "cid": int(self.cid),
            "sec": self.sec,
        }
        if self.device_id:
            payload["deviceId"] = self.device_id
        r = requests.post(f"{self.base_url}/auth/accesstokenrequest", json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        token = data.get("accessToken")
        if not token:
            raise RuntimeError(data.get("errorText") or "Tradovate did not return an access token.")
        self.access_token = token
        return data

    def _headers(self) -> dict[str, str]:
        if not self.access_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.access_token}"}

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        r = requests.get(f"{self.base_url}/{path.lstrip('/')}", headers=self._headers(), params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def accounts(self) -> list[dict[str, Any]]:
        return self.get("account/list")

    def positions(self) -> list[dict[str, Any]]:
        return self.get("position/list")

    def cash_balances(self) -> list[dict[str, Any]]:
        return self.get("cashBalance/list")

    def orders(self) -> list[dict[str, Any]]:
        return self.get("order/list")

    def account_snapshot(self) -> dict[str, Any]:
        accounts = self.accounts()
        positions = self.positions()
        balances = self.cash_balances()
        active = next((a for a in accounts if a.get("active")), accounts[0] if accounts else {})
        account_id = active.get("id")
        balance = next((b for b in balances if b.get("accountId") == account_id), balances[0] if balances else {})
        return {"account": active, "balance": balance, "positions": positions}

    def place_order(self, *_args, **_kwargs):
        raise RuntimeError("Order execution is disabled in this dashboard build.")
