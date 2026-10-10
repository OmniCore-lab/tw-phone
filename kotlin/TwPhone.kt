package dev.omnicorelab.twphone

/**
 * Shape rules for Taiwanese phone numbers. Mirrors ../python/tw_phone.py line for line;
 * see that file for what each kind means. Both are checked against ../cases.json.
 */
object TwPhone {
    private const val FW_FROM = "０１２３４５６７８９＋＃（）－．"
    private const val FW_TO = "0123456789+#()-."
    private val ZH = mapOf('零' to '0', '〇' to '0', '洞' to '0', '一' to '1', '么' to '1', '幺' to '1', '二' to '2', '兩' to '2', '三' to '3', '四' to '4',
        '五' to '5', '六' to '6', '七' to '7', '八' to '8', '九' to '9')
    private val EXT = Regex("""(?:#|轉|分機|ext\.?|EXT\.?|Ext\.?)\s*[0-9]{1,6}\s*$""")
    private val SHORT = setOf("110", "119", "112", "113", "117", "104", "105", "106", "123", "165", "166", "167", "168", "1922", "1925", "1950", "1955", "1957", "1966", "1980",
        "1985", "1988", "1990", "1995", "1996", "1999", "1910", "1911", "1912", "1968", "1998")
    private val CUE = Regex("(電話|市話|手機|家裡|公司|住家|打給|打到|撥|來電|回電|聯絡|連絡|專線|傳真|TEL|Tel|tel|Phone|phone|☎|📞)")
    private val MASKED = Regex("[*＊○●✦xX]")
    private val TAIL = Regex("(尾數|末碼|末[三四五]碼|後[三四五]碼)")
    private val R_FREE = Regex("080[09][0-9]{6}"); private val R_PAID = Regex("020[1-9][0-9]{6}"); private val R_BIZ = Regex("(?:412|405|407|449)[0-9]{4,5}")
    private val R_MOBILE = Regex("09[0-9]{8}"); private val R_VOIP = Regex("070[0-9]{8}")
    private val R_02 = Regex("02[2-9][0-9]{7}"); private val R_04 = Regex("04[2-9][0-9]{6,7}"); private val R_0X = Regex("0[35678][2-9][0-9]{6}")
    private val R_LOCAL = Regex("[2-9][0-9]{6,7}")

    /** Full-width to half-width, Chinese numerals to digits, strip the extension. Returns (starts with +, digits only). */
    fun digits(v: String): Pair<Boolean, String> {
        val sb = StringBuilder(v.length)
        for (ch in v) { val i = FW_FROM.indexOf(ch); sb.append(if (i >= 0) FW_TO[i] else ZH[ch] ?: ch) }
        val t = EXT.replace(sb.toString().trim(), "")
        val plus = t.trimStart(' ', '(').startsWith("+")
        return plus to t.filter { it in '0'..'9' }
    }

    fun classify(v: String): String? {
        var (plus, d) = digits(v)
        if (d.isEmpty()) return null
        if (d.startsWith("00886")) { d = "886" + d.substring(5); plus = true }
        if (d.startsWith("886") && (plus || d.length == 11 || d.length == 12)) {
            val rest = d.substring(3)
            d = if (rest.startsWith("0")) rest else "0$rest"
            plus = false
        }
        if (plus) return if (d.length in 8..15) "intl" else null
        return when {
            d in SHORT -> "service"
            R_FREE.matches(d) || R_PAID.matches(d) -> "service"
            R_BIZ.matches(d) -> "service"
            R_MOBILE.matches(d) -> "mobile"
            R_VOIP.matches(d) -> "landline"
            R_02.matches(d) || R_04.matches(d) || R_0X.matches(d) -> "landline"
            R_LOCAL.matches(d) -> "local"
            else -> null
        }
    }

    /** Something upstream says text[s, e) is a phone number. Is the shape right, and could it be a private number? */
    fun phoneOk(text: String, s: Int, e: Int): Boolean {
        val v = text.substring(s, e)
        if (MASKED.containsMatchIn(v)) return true          // already partly masked (0912-***-678): accept without checking the shape
        if (TAIL.containsMatchIn(v)) return true            // only the last digits are given (尾數203): accept
        val a = text.lastIndexOf('\n', s - 1) + 1
        val b = text.indexOf('\n', e).let { if (it < 0) text.length else it }
        val cue = CUE.containsMatchIn(text.substring(maxOf(a, s - 14), s) + " " + text.substring(e, minOf(b, e + 6)))
        return when (classify(v)) {
            "mobile", "landline", "intl" -> true
            "local" -> cue
            null -> {
                // one digit off: if the text says it is a phone and the length is off by one, still accept
                val d = digits(v).second
                cue && ((d.startsWith("09") && d.length in 9..11) || (d.length >= 2 && d[0] == '0' && d[1] in "2345678" && d.length in 8..11))
            }
            else -> false
        }
    }
}
