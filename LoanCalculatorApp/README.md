# Home Loan EMI Calculator - Android App

A comprehensive Android app for calculating home loan EMI and generating PDF reports.

## Features

- Calculate loan EMI with prepayments
- Support for Land Loan + Construction Loan
- Multiple prepayment schedules
- Generate detailed PDF reports
- Indian number formatting (Rs. XX,XX,XXX)
- Month-wise amortization schedule
- Works completely offline

## How to Build the APK

### Prerequisites

1. **Android Studio** (Download from: https://developer.android.com/studio)
2. **Java JDK 17** or higher

### Steps

1. **Open Android Studio**

2. **Open the project**
   - File → Open → Select the `LoanCalculatorApp` folder

3. **Wait for Gradle sync**
   - Android Studio will automatically download dependencies
   - This may take a few minutes the first time

4. **Build the APK**
   - Build → Build Bundle(s) / APK(s) → Build APK(s)
   - Or use: `./gradlew assembleDebug` in terminal

5. **Find the APK**
   - The APK will be at: `app/build/outputs/apk/debug/app-debug.apk`

6. **Install on device**
   - Transfer the APK to your Android phone
   - Enable "Install from unknown sources" in settings
   - Tap the APK to install

### Build Signed APK (for distribution)

1. Build → Generate Signed Bundle / APK
2. Select APK
3. Create a new keystore or use existing
4. Select release build type
5. Find APK at: `app/build/outputs/apk/release/`

## App Usage

1. Enter Land Loan amount
2. Enter Construction Loan amount (optional)
3. Select Loan Start Date
4. Select Construction Start Date (if applicable)
5. Enter Monthly EMI amount
6. Enter Interest Rate
7. Add up to 3 prepayment schedules
8. Tap "Calculate" to see results
9. Tap "Download PDF Report" to save PDF

## Technical Details

- **Min SDK:** Android 7.0 (API 24)
- **Target SDK:** Android 14 (API 34)
- **Language:** Kotlin
- **UI:** WebView with embedded HTML/JavaScript
- **PDF Generation:** Android PdfDocument API

## Project Structure

```
LoanCalculatorApp/
├── app/
│   ├── src/main/
│   │   ├── java/com/loancalculator/
│   │   │   ├── MainActivity.kt      # Main activity with WebView
│   │   │   └── PDFGenerator.kt      # PDF generation logic
│   │   ├── assets/
│   │   │   └── index.html           # Calculator UI
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   ├── values/
│   │   │   └── xml/
│   │   └── AndroidManifest.xml
│   └── build.gradle
├── build.gradle
├── settings.gradle
└── gradle.properties
```

## License

Free for personal and commercial use.
