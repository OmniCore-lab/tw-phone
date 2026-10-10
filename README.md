# tw-phone

Shape rules for Taiwanese phone numbers, in Python and Kotlin.

Given a fragment of text that might be a phone number, it tells you what kind it is, or that it is not one.

```
$ python python/tw_phone.py "0912-345-678" "091123456" "零九三二 六六一 二零三" "0800-080-123" "2345-6789"
0912-345-678               mobile
091123456                  None
零九三二 六六一 二零三       mobile
0800-080-123               service
2345-6789                  local
```

## Why

We work on software that has to notice personal information in everyday Chinese text. Statistical models are good at context and bad at counting: they learn that "digits starting with 09" look like a phone number and then flag nine-digit order numbers and six-digit codes too.

Phone numbers follow rules. So we let the model propose, and check the shape with rules.

## What it knows

| Kind | Meaning |
| --- | --- |
| `mobile` | 09 + 8 digits. Also `+886 9…`, `00886…`, full-width digits, and digits read aloud (零九三二…, 洞 for 0, 么 for 1) |
| `landline` | With area code: 02 + 8 digits; 03 / 05 / 06 / 07 / 08 + 7 digits (037, 049, 089, 082 included); 04 + 7 or 8 digits; 070 internet telephony |
| `local` | 7 or 8 digits with no area code. Digits alone can't tell, see `phone_ok` |
| `service` | Not a private number: 0800 / 0809, 020x, 412 / 405 business lines, short codes such as 110, 119, 165, 1922, 1999 |
| `intl` | Starts with `+`, 8 to 15 digits |
| `None` | Not shaped like a phone number |

Extensions (`#12`, `轉 12`, `分機 12`, `ext 12`) are ignored.

`phone_ok(text, start, end)` answers a slightly different question: something upstream thinks `text[start:end]` is a phone number that belongs to a person. Is that believable?

- `mobile`, `landline`, `intl`: yes
- `service`: no
- `local`: only if a word like 電話, 打給 or 市話 is next to it
- already partly masked (`0912-***-678`) or last digits only (`尾數203`): yes
- one digit too long or short, and the text says it is a phone: yes. Speech recognition drops digits; missing most of a number is still a miss.

## Use

Python, no dependencies:

```python
from tw_phone import classify, phone_ok

classify("(02)2345-6789 分機 12")        # "landline"
phone_ok("訂了 2345-6789 張", 3, 12)      # False
phone_ok("家裡電話 2345-6789", 5, 14)     # True
```

Kotlin: copy `kotlin/TwPhone.kt`. It uses only the standard library.

## Tests

`cases.json` holds 197 cases. Both implementations must give the same answer for every one.

```
python -m unittest discover tests
```

The Python side runs in CI here. The Kotlin port is checked against the same file in our app's own test suite.

## Limits

- Taiwan only. Other countries get `intl` if they start with `+`, and nothing more.
- It judges shape, not whether a number is in service.
- Numbering plans change. Corrections are welcome: open an issue with the number format and a source.

## License

MIT. Made by [OmniCore Lab](https://omnicore-lab.dev/).
