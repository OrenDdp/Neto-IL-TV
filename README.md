# Neto-IL-TV

Kodi עם התוסף עידן+ בלבד. בראש העמוד Dock של הקטגוריות (ערוצים חיים, VOD, המשך צפייה, מועדפים, ערוצי גיבוי), ומתחתיו גריד של אריחים גדולים. ל־LG יש גם גרסה עם לשוניות בצד.

> **הבהרה:** Neto-IL-TV הוא פרויקט פרטי ולא רשמי. הוא לא קשור לעידן+, ל־Fishenzon, ל־Kodi / XBMC Foundation, ל־POV או לאף ערוץ, ולא מאושר על ידם.
> הוא לא מכיל ולא מאחסן שום תוכן: כל השידורים וה־VOD מגיעים ישירות מהאתרים הרשמיים של הערוצים, דרך התוסף עידן+ של Fishenzon.
> בעל זכויות שרוצה שמשהו יוסר מכאן מוזמן לפתוח Issue.

![עמוד הבית: Dock למעלה וגריד של המועדפים](screenshots/favourites.png)

<p>
<img src="screenshots/icon.png" alt="האייקון" width="220">
<img src="screenshots/opening.png" alt="מסך הפתיחה" width="420">
</p>

התוסף עידן+ עצמו לא נמצא כאן. הוא של [Fishenzon](https://github.com/Fishenzon/repo), ומותקן אוטומטית מהמאגר שלו בהפעלה הראשונה (צריך חיבור לאינטרנט).

## התקנה

### אנדרואיד TV (Mi Box וכו')
באפליקציית **Downloader** מקלידים את הקוד **2738779**. הוא מוריד תמיד את הגרסה האחרונה.

או מורידים ישירות: [Neto-IL-TV-android.apk](https://github.com/OrenDdp/Neto-IL-TV/releases/latest/download/Neto-IL-TV-android.apk). מותקן לצד Kodi רגיל ולא נוגע בו.

### LG webOS
מורידים אחד מקובצי ה־IPK (Dock או לשוניות) מ־[Releases](../../releases/latest) ומתקינים במצב מפתחים (webOS Dev Manager, או `ares-install`).

### Kodi רגיל (21 ומעלה)
1. הגדרות > מערכת > הרחבות: להפעיל **מקורות לא ידועים**.
2. מנהל קבצים > הוסף מקור: `https://orenddp.github.io/Neto-IL-TV/`
3. הרחבות > התקנה מקובץ zip > המקור שהוספת > `repository.netotv-1.0.0.zip`
4. הרחבות > התקנה ממאגר > **Neto-IL-TV repository** > **Neto-IL-TV** > התקן.

Neto-IL-TV מוריד את עידן+, מעביר את Kodi לעברית ולסקין שלו, ומוסיף את הלשוניות.

## בשלט
- **Back** בזמן צפייה: עוצר וחוזר לרשימה.
- **Back** בתפריט הצד: מסתיר את האפליקציה.
- **כפתור אדום** (בשלט LG): תפריט הפריט, למשל "הוסף למועדפי עידן פלוס".
- סוג התצוגה של כל לשונית: גלגל שיניים > Skin settings > פריטי תפריט ראשי > Set widgets > Widget 1 > Display type.

## מה יש כאן
| תיקייה | מה |
|---|---|
| `src/service.netotv` | מתקין את עידן+, מגדיר את Kodi ורושם את הלשוניות |
| `src/plugin.video.netotv` | מפצל את הערוצים החיים לערוצים רגילים וערוצי גיבוי |
| `src/skin.fentastic` | [FENtastic](https://github.com/ivarbrandt/skin.fentastic) של Ivar Brandt (GPL-2.0 / CC BY-SA 4.0), עם תפריט הלשוניות, לוגו, צבעים ותצוגות Grid |
| `src/script.fentastic.helper` | העוזר של FENtastic (GPL-2.0), עם ברירות המחדל של הלשוניות ותצוגות Grid |
| `kodi-changes/` | כל מה ששונה ב־Kodi עצמו, כ־diff מול הגרסה הרשמית |
| `docs/` | מאגר ה־Kodi (GitHub Pages) |
| `tools/`, `webos/`, `build.sh` | בניית הלשוניות, הלוגו, המאגר, ה־APK וה־IPK |

## רישיונות
- קבצי ההתקנה מבוססים על [Kodi](https://kodi.tv) הרשמי (GPL-2.0); הקוד המלא ב־[xbmc/xbmc](https://github.com/xbmc/xbmc), והשינויים שלנו ב־`kodi-changes/`. "Kodi" הוא סימן מסחרי של XBMC Foundation; Neto-IL-TV לא משתמש בשם או בלוגו של Kodi כשם המוצר.
- FENtastic והעוזר שלו: GPL-2.0 (קוד), CC BY-SA 4.0 (גרפיקה), של Ivar Brandt ו־Tikipeter.
- הקוד שלנו (`src/service.netotv`, `src/plugin.video.netotv`, `tools/`, `webos/`): GPL-2.0.
