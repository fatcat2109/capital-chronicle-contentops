"""CC-466 plan pages inside the CC-436 Neo transport and sole coordinator.

Only bound WEB_ONLY plan pages and CC-536 research pieces are accepted. This is no alternate
publisher: claims, exactly-once, pending codes and reconciliation stay native.
"""
from __future__ import annotations

from html import escape
import re

from .neo_destination_handoff_v1 import _text, _substack_rendered_text


def body_html(text):
    blocks=[]
    for block in text.split("\n\n"):
        if block.startswith("## "):
            blocks.append("<h2>"+escape(block[3:])+"</h2>")
        elif block.startswith("|"):
            rows=[line for line in block.splitlines() if not re.fullmatch(r"[| :\-]+",line)]
            blocks.append("<table>"+"".join("<tr>"+"".join("<td>"+escape(cell.strip())+"</td>"
                for cell in line.strip("|").split("|"))+"</tr>" for line in rows)+"</table>")
        else:
            blocks.extend("<p>"+escape(line)+"</p>" for line in block.splitlines())
    return "".join(blocks)


def _ref(client,page,role,name):
    values=[r for r in client.snapshot(page)["refs"] if r["role"]==role and r["name"]==name]
    if not values:
        raise ValueError("PLAN_SUBSTACK_CONTROL_MISSING:"+name)
    return values[-1]["ref"]


def perform(client, packet):
    from .neo_endpoint_executor_v1 import NeoEndpointError
    from requests import RequestException
    state={"identity":{},"dispatched_at_utc":None}
    try:
        return _perform(client,packet,state)
    except (NeoEndpointError,RequestException,ValueError,KeyError,OSError) as exc:
        # A failed editor check precedes the publish click. After a click or
        # a lost click return only readback may resolve the attempt.
        attempted=state["dispatched_at_utc"] is not None
        read=request_action(packet)=="READBACK"
        return {"result":{"status":"READBACK_UNAVAILABLE" if read else "UNKNOWN_WRITE" if attempted else "FAILED_BEFORE_WRITE",
            "definite_no_write":not attempted,"public_write_performed":False if not attempted else None,
            "stage":"PUBLISH_CLICK_ATTEMPTED" if attempted else "BEFORE_PUBLISH_CLICK",
            "reason_code":str(exc)[:160]},"identity":state["identity"],
            "dispatched_at_utc":state["dispatched_at_utc"]}


def request_action(packet):
    return (packet.get("request") or {}).get("action")


def supports_operation(operation_id):
    return (operation_id.startswith("plan-analysis-")
            or re.fullmatch(r"cc536-measured-odds-[1-7]", operation_id) is not None)


def body_text(text):
    return _substack_rendered_text(re.sub(r"^## ","",text,flags=re.M))


def _perform(client, packet, state):
    request=packet["request"]
    if not supports_operation(packet["operation_id"]) or request["destination"]!="substack":
        raise ValueError("PLAN_SUBSTACK_EXACT_PAGE_REQUEST_REQUIRED")
    page=client.open("plan-substack", request.get("public_object_url") or "https://capitalchronicle.substack.com/publish/posts")
    if request["action"]=="READBACK":
        return {"result":readback(client,request,page),"identity":{}}
    client.wait(page,'nav[aria-label="Publisher dashboard"]')
    identity=client.run(page,"plan_substack_identity")
    state["identity"]=identity
    if request["action"]=="VERIFY_IDENTITY":
        return {"result":{**identity,"status":"SUCCESS"},"identity":identity}
    if request["action"]!="PUBLISH" or request.get("substack_delivery_policy",{}).get("email_send_enabled") is not False:
        raise ValueError("PLAN_SUBSTACK_WEB_ONLY_REQUIRED")
    if not identity.get("authenticated"):
        return {"result":{"status":"FAILED_BEFORE_WRITE","definite_no_write":True,
            "public_write_performed":False,"stage":"BEFORE_PUBLISH_CLICK",
            "reason_code":"NEO_SIGNED_IN_ACCOUNT_MISMATCH"},"identity":identity}
    payload=request["native_payload"]
    # Native page requests contain the exact manuscript; no article compiler or
    # model rewrites it at transport time.
    client.act(page,"click",ref=_ref(client,page,"button","Create"))
    client.wait_text(page,"Article")
    client.act(page,"click",ref=_ref(client,page,"menuitem","Article"))
    client.wait(page,".ProseMirror")
    client.act(page,"fill",ref=_ref(client,page,"textbox","title"),value=payload["title"])
    client.act(page,"fill",ref=_ref(client,page,"textbox","Add a subtitle…"),value=payload["subtitle"])
    media=(request.get("content_binding") or {}).get("media_manifest") or []
    if len(media)>1:
        raise ValueError("PLAN_SUBSTACK_ONE_BOUND_CHART_REQUIRED")
    original_src=None
    if media:
        client.run(page,"plan_substack_intercept")
        client.act(page,"click",ref=_ref(client,page,"button","Insert image"))
        client.wait_text(page,"Gallery")
        client.act(page,"click",ref=_ref(client,page,"menuitem","Image"))
        client.wait(page,'[aria-label="CC466 editor upload"]')
        client.call("upload",{"page":page,"ref":_ref(client,page,"button","CC466 editor upload"),
                              "files":[media[0]["path"]]})
        client.wait(page,".ProseMirror img")
        original_src=client.run(page,"plan_substack_uploaded")["src"]
    html=body_html(payload["body_markdown"])
    if media:
        asset=media[0]
        figure='<figure><img src="'+escape(original_src,quote=True)+'" alt="'+escape(asset.get("alt_text",""),quote=True)+'"><figcaption>'+escape(asset.get("caption",""))+'</figcaption></figure>'
        # The reader contract places the chart after its At a glance block.
        index=html.index("<h2>") if "<h2>" in html else len(html)
        html=html[:index]+figure+html[index:]
    client.run(page,"plan_substack_clear")
    client.wait(page,".ProseMirror:not(:has(h2)):not(:has(img))")
    client.run(page,"plan_substack_paste",html=html)
    client.wait(page,".ProseMirror h2")
    check=client.run(page,"plan_substack_check",expected_text=body_text(payload["body_markdown"]),media=media)
    if check.get("verified") is not True:
        raise ValueError("PLAN_SUBSTACK_EXACT_DRAFT_MISMATCH")
    client.act(page,"click",ref=_ref(client,page,"button","Continue"))
    client.wait_text(page,"Send via email and the Substack app")
    if client.run(page,"plan_substack_email")["enabled"]:
        client.act(page,"click",ref=_ref(client,page,"checkbox","Send via email and the Substack app"))
        client.wait_text(page,"Publish now")
    # This phase refuses a still-enabled email or schedule before the one click.
    # Mark the boundary before the tool call: a lost click return is uncertain.
    from datetime import datetime, timezone
    state["dispatched_at_utc"]=datetime.now(timezone.utc).isoformat()
    published=client.run(page,"plan_substack_publish")
    if published.get("status")!="CLICKED":
        if published.get("definite_no_write") is True:
            state["dispatched_at_utc"]=None
        return {"result":published,"identity":identity}
    state["dispatched_at_utc"]=published["dispatched_at_utc"]
    follow=wait_or_code(client,page,"Publish on web only")
    if "Check your email" in follow["text"]:
        return pending_code(client,page,published,identity)
    client.act(page,"click",ref=_ref(client,page,"button","Publish on web only"))
    follow=wait_or_code(client,page,"Copy link")
    if "Check your email" in follow["text"]:
        return pending_code(client,page,published,identity)
    public=client.run(page,"plan_substack_published")
    if not public.get("public_object_url"):
        return {"result":{"status":"UNKNOWN_WRITE","stage":"PUBLISH_CLICK_ATTEMPTED"},"identity":identity}
    return {"result":{**public,"status":"SUCCESS","observed_identity":"capitalchronicle.substack.com",
        "stage":"PUBLISH_CLICK_ATTEMPTED","delivery_observation":{"email_send_enabled":False,
            "web_publish_enabled":True,"evidence_ref":"Neo unchecked email and web-only confirmation; same tab reached share-center."}},
        "identity":identity,"dispatched_at_utc":published["dispatched_at_utc"]}


def wait_or_code(client,page,text):
    from .neo_endpoint_executor_v1 import NeoEndpointError
    try:
        client.wait_text(page,text)
    except (NeoEndpointError,ValueError):
        observed=client.snapshot(page)
        if "Check your email" in observed["text"]:
            return observed
        raise
    return client.snapshot(page)


def pending_code(client,page,published,identity):
    # Open, never inspect, the mailbox only after the observed code dialog.
    opened=client.run(page,"plan_substack_code_handoff")
    return {"result":{"status":"PENDING_JIM_EMAIL_CODE",**opened,
        "public_write_performed":False},"identity":identity,
        "dispatched_at_utc":published["dispatched_at_utc"]}


def readback(client,request,page):
    if not request.get("public_object_url"):
        return {"status":"READBACK_UNAVAILABLE","verified":False,
                "reason_code":"PLAN_SUBSTACK_EXACT_PUBLIC_URL_REQUIRED"}
    client.wait_text(page,request["native_payload"]["title"])
    result=client.run(page,"plan_substack_readback")
    if result.get("public_object_url") == request["public_object_url"]:
        result["public_object_id"]=request["public_object_id"]
        result["object_id_basis"]="EXACT_CANONICAL_URL_BOUND_TO_OBSERVED_SHARE_CENTER_ID"
    # Reuse CC-436's bounded binary checks. Substack's original uploaded PNG
    # is visible in its rendered figure URL and keeps exact original bytes.
    from .neo_endpoint_executor_v1 import compare_public_images
    observed=compare_public_images(request,result,http=getattr(client,"image_http",None))
    captions=[a.get("caption","") for a in request["content_binding"].get("media_manifest",[])]
    comparison=_text(result.get("observed_text",""))
    for caption in captions:
        comparison=_text(comparison.replace(_text(caption)," "))
    expected=request["content_binding"].get("media_manifest",[])
    actual=result.get("media",[])
    article=_text(result.get("article_text",""))
    for caption in captions:
        article=_text(article.replace(_text(caption)," "))
    observed["content_verified"]=(all(_substack_rendered_text(s) in comparison
        for s in request["content_binding"]["expected_text_segments"])
        and article==body_text(request["native_payload"]["body_markdown"])
        and len(expected)==len(actual) and all(a.get("alt_text")==b.get("alt_text")
            and _text(a.get("caption"))==_text(b.get("caption")) for a,b in zip(expected,actual)))
    return observed
