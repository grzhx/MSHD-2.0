from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from codec import codec
from codec import dictionaries as dicts
from codec.models import DecodedRecord

app = FastAPI(title="MSHD2.0 Codec Service", version="0.1.0")


class EncodeRequest(BaseModel):
    event: dict
    source: dict
    carrier: dict
    disaster: dict


@app.post("/api/codec/encode")
def encode(req: EncodeRequest):
    try:
        event = codec.build_event_info(
            req.event["locationCode"], req.event["time"]
        )
        source = codec.build_source_info(req.source["code"])
        carrier = codec.build_carrier_info(req.carrier["code"])
        disaster = codec.build_disaster_info(
            req.disaster["categoryCode"],
            req.disaster["subCategoryCode"],
            req.disaster["indicatorCode"],
        )
        encoded_id = codec.encode_disaster(event, source, carrier, disaster)
        return {"id": encoded_id}
    except Exception as exc:  # concise error surfacing
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/codec/decode/{encoded_id}", response_model=DecodedRecord)
def decode(encoded_id: str):
    try:
        return codec.decode_disaster(encoded_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/dict/{domain}")
def list_domain(domain: str):
    try:
        return dicts.list_domain(domain)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/dict/{domain}/{code}")
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})
