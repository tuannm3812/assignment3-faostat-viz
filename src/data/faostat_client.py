"""Small FAOSTAT API client used by the data pipeline.

Secrets are read from environment variables only. Do not hard-code access
tokens in this file or commit them to the repository.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
BASE_URL = "https://faostatservices.fao.org/api/v1"


class FaostatApiError(RuntimeError):
    """Raised when the FAOSTAT API returns an error response."""


def get_access_token() -> str:
    load_dotenv(ROOT_DIR / ".env")
    token = os.getenv("FAOSTAT_ACCESS_TOKEN", "").strip()
    if not token:
        raise FaostatApiError("Set FAOSTAT_ACCESS_TOKEN in your environment or .env file.")
    return token


def faostat_get(path: str, params: Any | None = None, language: str = "en") -> dict[str, Any]:
    token = get_access_token()
    clean_path = path.strip("/")
    if not clean_path.startswith(f"{language}/"):
        clean_path = f"{language}/{clean_path}"

    response = requests.get(
        f"{BASE_URL}/{clean_path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=60,
    )
    if response.status_code >= 400:
        raise FaostatApiError(f"FAOSTAT API error {response.status_code}: {response.text[:500]}")
    return response.json()


def response_to_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    """Convert common FAOSTAT response shapes into a dataframe."""
    for key in ("data", "Data", "results", "value"):
        records = payload.get(key)
        if isinstance(records, list):
            return pd.json_normalize(records)
    if isinstance(payload, list):
        return pd.json_normalize(payload)
    return pd.json_normalize(payload)


def get_groups_and_domains(language: str = "en") -> pd.DataFrame:
    payload = faostat_get("groupsanddomains", language=language)
    return response_to_dataframe(payload)


def get_domain_data(domain: str, params: Any, language: str = "en") -> pd.DataFrame:
    payload = faostat_get(f"data/{domain}", params=params, language=language)
    return response_to_dataframe(payload)


def save_domain_data(domain: str, params: Any, output_path: Path, language: str = "en") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = get_domain_data(domain=domain, params=params, language=language)
    df.to_csv(output_path, index=False)
    return output_path


def parse_param_pairs(values: list[str]) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = []
    for value in values:
        if "=" not in value:
            raise argparse.ArgumentTypeError(f"Parameter must use key=value format: {value}")
        key, item = value.split("=", 1)
        params.append((key, item))
    return params


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch FAOSTAT data into a local CSV.")
    parser.add_argument("--domain", required=True, help="FAOSTAT domain code, for example PP or QCL.")
    parser.add_argument("--param", action="append", default=[], help="Query parameter as key=value. Repeat as needed.")
    parser.add_argument("--output", required=True, help="Output CSV path.")
    parser.add_argument("--language", default="en", help="FAOSTAT language code. Default: en.")
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ROOT_DIR / output_path

    saved = save_domain_data(
        domain=args.domain,
        params=parse_param_pairs(args.param),
        output_path=output_path,
        language=args.language,
    )
    print(f"Saved FAOSTAT data to {saved}")


if __name__ == "__main__":
    main()
