import logging
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .codec import codec as codec_core
from .codec import dictionaries as dicts
from .codec.models import DecodedRecord

router = APIRouter()
logger = logging.getLogger(__name__)


class EncodeRequest(BaseModel):
    event: dict
    source: dict
    carrier: dict
    disaster: dict


@router.post("/api/codec/encode")
def encode(req: EncodeRequest):
    try:
        logger.info("Encoding request received event=%s source=%s", req.event, req.source)
        event = codec_core.build_event_info(req.event["locationCode"], req.event["time"])
        source = codec_core.build_source_info(req.source["code"])
        carrier = codec_core.build_carrier_info(req.carrier["code"])
        disaster = codec_core.build_disaster_info(
            req.disaster["categoryCode"],
            req.disaster["subCategoryCode"],
            req.disaster["indicatorCode"],
        )
        encoded_id = codec_core.encode_disaster(event, source, carrier, disaster)
        return {"id": encoded_id}
    except Exception as exc:
        logger.exception("Encode failed for payload=%s", req.model_dump())
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/codec/decode/{encoded_id}", response_model=DecodedRecord)
def decode(encoded_id: str):
    try:
        logger.info("Decoding request id=%s", encoded_id)
        return codec_core.decode_disaster(encoded_id)
    except Exception as exc:
        logger.exception("Decode failed for id=%s", encoded_id)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _flatten_domain(domain: str, data: Dict) -> List[Dict[str, str]]:
    """
    将嵌套字典展开成 {code, name} 列表，便于前端直接展示。
    """
    if domain == "carrier":
        return [{"code": code, "name": name} for code, name in data.items()]

    if domain == "source":
        flat = []
        for cat, sub_map in data.items():
            for sub, name in sub_map.items():
                flat.append({"code": f"{cat}{sub}", "name": name})
        return flat

    if domain == "disaster":
        flat = []
        for cat, sub_map in data.items():
            for sub, name in sub_map.items():
                flat.append({"code": f"{cat}{sub}", "name": name})
        return flat

    if domain == "indicator":
        flat = []
        for cat, sub_map in data.items():
            for sub, ind_map in sub_map.items():
                for ind, name in ind_map.items():
                    flat.append({"code": f"{cat}{sub}{ind}", "name": name})
        return flat

    return []


@router.get("/api/dict/{domain}")
def list_domain(domain: str, flat: bool = Query(False, description="是否返回扁平数组 {code,name}")):
    try:
        data = dicts.list_domain(domain)
        logger.info("Dictionary domain=%s flat=%s", domain, flat)
        if flat:
            return _flatten_domain(domain, data)
        return data
    except Exception as exc:
        logger.exception("Dictionary lookup failed for domain=%s", domain)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/dict/{domain}/{code}")
def get_code(domain: str, code: str):
    try:
        if domain == "source":
            name = dicts.get_source_name(code)
        elif domain == "carrier":
            name = dicts.get_carrier_name(code)
        elif domain == "disaster":
            if len(code) != 3:
                raise ValueError("disaster code must be 3 digits: dcc")
            cat, sub = code[0], code[1:]
            name = dicts.DISASTER_CATEGORY_DICT.get(cat, {}).get(sub)
        elif domain == "indicator":
            if len(code) != 6:
                raise ValueError("indicator code must be 6 digits: dcciii")
            cat, sub, ind = code[0], code[1:3], code[3:]
            name = dicts.DISASTER_INDICATOR_DICT.get(cat, {}).get(sub, {}).get(ind)
        else:
            raise ValueError("unknown domain")
        if name is None:
            raise ValueError("code not found")
        return {"code": code, "name": name}
    except Exception as exc:
        logger.exception("Dictionary lookup failed for domain=%s code=%s", domain, code)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/health")
def health():
    return JSONResponse({"status": "ok"})
