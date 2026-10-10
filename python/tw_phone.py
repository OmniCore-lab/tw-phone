"""Shape rules for Taiwanese phone numbers.

A statistical model learns that "a run of digits starting with 09 looks like a phone number" and then
calls nine-digit and six-digit strings phones as well. Phone numbers follow rules, so check them with rules.

classify(fragment) returns:
  mobile    09 + 8 digits (also +886 9..., and digits read aloud in Chinese: 零九三二...)
  landline  with area code: 02 + 8 digits; 03/05/06/07/08 + 7 digits (longer area codes such as 037, 049, 089, 082
            have the same total length); 04 + 7 or 8 digits; 070 internet telephony
  local     landline without an area code: 7 or 8 digits starting 2-9. Digits alone cannot tell, so
            phone_ok() only accepts it when a word such as 電話 / 打給 / 市話 is nearby
  service   not a private number: 0800 / 0809 toll-free, 020x premium, 412 / 405 business lines,
            and short codes (110, 119, 165, 1922, 1999 ...)
  intl      other countries: starts with +, 8-15 digits
  None      not shaped like a phone number (wrong length or prefix)
Extensions (#12, 轉 12, 分機 12, ext 12) do not affect the result.

The Kotlin port in ../kotlin/TwPhone.kt mirrors this file line for line; both are checked against ../cases.json.
"""
import re

_FW = str.maketrans("０１２３４５６７８９＋＃（）－．", "0123456789+#()-.")
_ZH = str.maketrans({"零": "0", "〇": "0", "洞": "0", "一": "1", "么": "1", "幺": "1", "二": "2", "兩": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"})
_EXT = re.compile(r"(?:#|轉|分機|ext\.?|EXT\.?|Ext\.?)\s*[0-9]{1,6}\s*$")
_SHORT = {"110", "119", "112", "113", "117", "104", "105", "106", "123", "165", "166", "167", "168", "1922", "1925", "1950", "1955", "1957", "1966", "1980", "1985", "1988", "1990", "1995", "1996", "1999",
          "1910", "1911", "1912", "1968", "1998"}
CUE = re.compile(r"(電話|市話|手機|家裡|公司|住家|打給|打到|撥|來電|回電|聯絡|連絡|專線|傳真|TEL|Tel|tel|Phone|phone|☎|📞)")


def digits(v):
    """Full-width to half-width, Chinese numerals to digits, strip the extension. Returns (starts with +, digits only)."""
    t = v.translate(_FW).translate(_ZH).strip()
    t = _EXT.sub("", t)
    plus = t.lstrip(" (").startswith("+")
    return plus, re.sub(r"[^0-9]", "", t)


def classify(v):
    plus, d = digits(v)
    if not d: return None
    # Country code 886: +886 9..., 00886..., 886-2-... (a bare 886 only counts when the length fits exactly)
    if d.startswith("00886"): d, plus = "886" + d[5:], True
    if d.startswith("886") and (plus or len(d) in (11, 12)):
        rest = d[3:]
        d = rest if rest.startswith("0") else "0" + rest
        plus = False
    if plus: return "intl" if 8 <= len(d) <= 15 else None
    if d in _SHORT: return "service"
    if re.fullmatch(r"080[09][0-9]{6}", d) or re.fullmatch(r"020[1-9][0-9]{6}", d): return "service"
    if re.fullmatch(r"(?:412|405|407|449)[0-9]{4,5}", d): return "service"
    if re.fullmatch(r"09[0-9]{8}", d): return "mobile"
    if re.fullmatch(r"070[0-9]{8}", d): return "landline"
    if re.fullmatch(r"02[2-9][0-9]{7}", d): return "landline"
    if re.fullmatch(r"04[2-9][0-9]{6,7}", d): return "landline"
    if re.fullmatch(r"0[35678][2-9][0-9]{6}", d): return "landline"
    if re.fullmatch(r"[2-9][0-9]{6,7}", d): return "local"
    return None


def phone_ok(text, s, e):
    """Something upstream says text[s:e] is a phone number. Is the shape right, and could it be a private number?"""
    v = text[s:e]
    if re.search(r"[*＊○●✦xX]", v): return True          # already partly masked (0912-***-678): accept without checking the shape
    if re.search(r"(尾數|末碼|末[三四五]碼|後[三四五]碼)", v): return True   # only the last digits are given (尾數203): accept
    k = classify(v)
    if k in ("mobile", "landline", "intl"): return True
    a = text.rfind("\n", 0, s) + 1; b = text.find("\n", e); b = len(text) if b < 0 else b
    cue = bool(CUE.search(text[max(a, s - 14):s] + " " + text[e:min(b, e + 6)]))
    if k == "local": return cue
    if k is None and cue:
        # one digit off (speech recognition dropped a digit, a key was hit twice): if the text says it is a phone and the length is off by one, still accept
        _, d = digits(v)
        if d.startswith("09") and 9 <= len(d) <= 11: return True
        if len(d) >= 2 and d[0] == "0" and d[1] in "2345678" and 8 <= len(d) <= 11: return True
    return False


if __name__ == "__main__":
    import sys
    for t in sys.argv[1:] or ["0912-345-678", "091123456", "零九三二 六六一 二零三", "+886 912 345 678", "02-2345-6789", "(04)2234-5678", "0800-080-123", "1999", "2345-6789", "+81 90 1234 5678"]:
        print(f"{t:26s} {classify(t)}")
