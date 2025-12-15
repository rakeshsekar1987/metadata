package com.loancalculator

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.pdf.PdfDocument
import android.os.Environment
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.text.DecimalFormat
import java.text.SimpleDateFormat
import java.util.*

class PDFGenerator(private val context: Context) {
    
    private val pageWidth = 595  // A4 width in points
    private val pageHeight = 842 // A4 height in points
    private val margin = 40f
    private val lineHeight = 18f
    
    private val titlePaint = Paint().apply {
        color = Color.parseColor("#1a237e")
        textSize = 24f
        isFakeBoldText = true
        isAntiAlias = true
    }
    
    private val headingPaint = Paint().apply {
        color = Color.parseColor("#1565c0")
        textSize = 16f
        isFakeBoldText = true
        isAntiAlias = true
    }
    
    private val subHeadingPaint = Paint().apply {
        color = Color.parseColor("#1976d2")
        textSize = 14f
        isFakeBoldText = true
        isAntiAlias = true
    }
    
    private val textPaint = Paint().apply {
        color = Color.parseColor("#37474f")
        textSize = 11f
        isAntiAlias = true
    }
    
    private val boldTextPaint = Paint().apply {
        color = Color.parseColor("#37474f")
        textSize = 11f
        isFakeBoldText = true
        isAntiAlias = true
    }
    
    private val highlightPaint = Paint().apply {
        color = Color.parseColor("#2e7d32")
        textSize = 20f
        isFakeBoldText = true
        isAntiAlias = true
    }
    
    private val tablePaint = Paint().apply {
        color = Color.parseColor("#e0e0e0")
        style = Paint.Style.STROKE
        strokeWidth = 1f
    }
    
    private val tableHeaderBg = Paint().apply {
        color = Color.parseColor("#1565c0")
        style = Paint.Style.FILL
    }
    
    private val whiteTextPaint = Paint().apply {
        color = Color.WHITE
        textSize = 10f
        isFakeBoldText = true
        isAntiAlias = true
    }
    
    private val smallTextPaint = Paint().apply {
        color = Color.parseColor("#757575")
        textSize = 9f
        isAntiAlias = true
    }
    
    fun formatIndianNumber(num: Double): String {
        if (num == 0.0) return "0"
        val rounded = num.toLong()
        val str = rounded.toString()
        if (str.length <= 3) return str
        
        val result = StringBuilder()
        var count = 0
        for (i in str.length - 1 downTo 0) {
            if (count == 3 || (count > 3 && (count - 3) % 2 == 0)) {
                result.insert(0, ',')
            }
            result.insert(0, str[i])
            count++
        }
        return result.toString()
    }
    
    fun formatRupees(num: Double): String {
        return "Rs. ${formatIndianNumber(num)}"
    }
    
    fun generateLoanPDF(jsonData: String): File {
        val data = JSONObject(jsonData)
        
        val document = PdfDocument()
        var pageNumber = 1
        var currentY = margin
        
        // Create first page
        var pageInfo = PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNumber).create()
        var page = document.startPage(pageInfo)
        var canvas = page.canvas
        
        // Title
        currentY += 60f
        canvas.drawText("HOME LOAN PAYOFF PLAN", pageWidth / 2f - 130f, currentY, titlePaint)
        
        currentY += 30f
        canvas.drawText("Comprehensive Month-wise Repayment Strategy", pageWidth / 2f - 140f, currentY, textPaint)
        
        // Key highlight box
        currentY += 50f
        val boxPaint = Paint().apply {
            color = Color.parseColor("#1565c0")
            style = Paint.Style.FILL
        }
        canvas.drawRect(margin, currentY, pageWidth - margin, currentY + 80f, boxPaint)
        
        canvas.drawText("PROJECTED LOAN CLOSURE", pageWidth / 2f - 80f, currentY + 25f, whiteTextPaint)
        
        val closureDate = data.optString("closure_date", "-")
        val bigWhitePaint = Paint().apply {
            color = Color.WHITE
            textSize = 22f
            isFakeBoldText = true
            isAntiAlias = true
        }
        canvas.drawText(closureDate, pageWidth / 2f - 40f, currentY + 50f, bigWhitePaint)
        
        val tenure = data.optString("tenure", "-")
        val tenureMonths = data.optInt("tenure_months", 0)
        canvas.drawText("Month $tenureMonths | $tenure", pageWidth / 2f - 60f, currentY + 70f, whiteTextPaint)
        
        // Summary metrics
        currentY += 120f
        val totalPrincipal = data.optDouble("total_principal", 0.0)
        val totalInterest = data.optDouble("total_interest", 0.0)
        val totalPaid = data.optDouble("total_paid", 0.0)
        
        val metricWidth = (pageWidth - 2 * margin) / 3
        
        canvas.drawText("Total Principal", margin + 20f, currentY, smallTextPaint)
        canvas.drawText(formatRupees(totalPrincipal), margin + 20f, currentY + 20f, highlightPaint)
        
        canvas.drawText("Total Interest", margin + metricWidth + 20f, currentY, smallTextPaint)
        val interestPaint = Paint().apply {
            color = Color.parseColor("#d32f2f")
            textSize = 20f
            isFakeBoldText = true
            isAntiAlias = true
        }
        canvas.drawText(formatRupees(totalInterest), margin + metricWidth + 20f, currentY + 20f, interestPaint)
        
        canvas.drawText("Total Paid", margin + 2 * metricWidth + 20f, currentY, smallTextPaint)
        val bluePaint = Paint().apply {
            color = Color.parseColor("#1565c0")
            textSize = 20f
            isFakeBoldText = true
            isAntiAlias = true
        }
        canvas.drawText(formatRupees(totalPaid), margin + 2 * metricWidth + 20f, currentY + 20f, bluePaint)
        
        // Loan Details Section
        currentY += 80f
        canvas.drawText("LOAN ASSUMPTIONS & PARAMETERS", margin, currentY, headingPaint)
        currentY += 5f
        canvas.drawLine(margin, currentY, pageWidth - margin, currentY, tablePaint)
        
        currentY += 30f
        val landLoan = data.optDouble("land_loan", 0.0)
        val constructionLoan = data.optDouble("construction_loan", 0.0)
        val emiAmount = data.optDouble("emi_amount", 0.0)
        val interestRate = data.optDouble("interest_rate", 0.0)
        val startDate = data.optString("start_date", "-")
        
        val details = listOf(
            "Interest Rate: $interestRate% p.a. (Monthly Reducing Balance)",
            "Land Loan: ${formatRupees(landLoan)}",
            if (constructionLoan > 0) "Construction Loan: ${formatRupees(constructionLoan)}" else null,
            "Total Principal: ${formatRupees(totalPrincipal)}",
            "Monthly EMI: ${formatRupees(emiAmount)}",
            "Loan Start: $startDate",
            "Projected Closure: $closureDate",
            "Effective Tenure: $tenure"
        ).filterNotNull()
        
        for (detail in details) {
            canvas.drawText("• $detail", margin + 10f, currentY, textPaint)
            currentY += lineHeight
        }
        
        // Key Financial Outcomes
        currentY += 30f
        canvas.drawText("KEY FINANCIAL OUTCOMES", margin, currentY, headingPaint)
        currentY += 5f
        canvas.drawLine(margin, currentY, pageWidth - margin, currentY, tablePaint)
        
        currentY += 20f
        val outcomes = listOf(
            Pair("Total Principal Borrowed", formatRupees(totalPrincipal)),
            Pair("Total EMI Payments", formatRupees(data.optDouble("total_emi", 0.0))),
            Pair("Total Prepayments", formatRupees(data.optDouble("total_prepayments", 0.0))),
            Pair("Total Amount Paid", formatRupees(totalPaid)),
            Pair("Total Interest Paid", formatRupees(totalInterest))
        )
        
        for ((label, value) in outcomes) {
            canvas.drawText(label, margin + 10f, currentY, textPaint)
            canvas.drawText(value, margin + 250f, currentY, boldTextPaint)
            currentY += lineHeight + 5f
        }
        
        // Part Payments
        val partPayments = data.optJSONArray("part_payments")
        if (partPayments != null && partPayments.length() > 0) {
            currentY += 20f
            canvas.drawText("PREPAYMENT SCHEDULE", margin, currentY, headingPaint)
            currentY += 5f
            canvas.drawLine(margin, currentY, pageWidth - margin, currentY, tablePaint)
            currentY += 20f
            
            for (i in 0 until partPayments.length()) {
                val pp = partPayments.getJSONObject(i)
                val month = pp.optString("month", "")
                val amount = pp.optDouble("amount", 0.0)
                canvas.drawText("• $month (Every Year): ${formatRupees(amount)}", margin + 10f, currentY, textPaint)
                currentY += lineHeight
            }
        }
        
        // Footer
        currentY = pageHeight - margin - 30f
        canvas.drawLine(margin, currentY, pageWidth - margin, currentY, tablePaint)
        currentY += 15f
        val dateFormat = SimpleDateFormat("MMMM dd, yyyy 'at' HH:mm", Locale.getDefault())
        canvas.drawText("Generated on ${dateFormat.format(Date())}", margin, currentY, smallTextPaint)
        canvas.drawText("Home Loan EMI Calculator App", pageWidth - margin - 150f, currentY, smallTextPaint)
        
        document.finishPage(page)
        
        // Monthly Schedule Pages
        val monthlySchedule = data.optJSONArray("monthly_schedule")
        if (monthlySchedule != null && monthlySchedule.length() > 0) {
            val rowsPerPage = 35
            var rowIndex = 0
            
            while (rowIndex < monthlySchedule.length()) {
                pageNumber++
                pageInfo = PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNumber).create()
                page = document.startPage(pageInfo)
                canvas = page.canvas
                currentY = margin
                
                // Page title
                canvas.drawText("MONTH-WISE AMORTIZATION SCHEDULE", margin, currentY + 20f, headingPaint)
                currentY += 40f
                
                // Table header
                val colWidths = floatArrayOf(35f, 60f, 80f, 65f, 70f, 70f, 65f, 80f)
                val headers = arrayOf("#", "Month", "Opening", "Interest", "Disbursal", "EMI", "Prepay", "Closing")
                
                canvas.drawRect(margin, currentY, pageWidth - margin, currentY + 20f, tableHeaderBg)
                
                var colX = margin + 5f
                for (i in headers.indices) {
                    canvas.drawText(headers[i], colX, currentY + 14f, whiteTextPaint)
                    colX += colWidths[i]
                }
                currentY += 20f
                
                // Table rows
                val tableTextPaint = Paint().apply {
                    color = Color.parseColor("#37474f")
                    textSize = 9f
                    isAntiAlias = true
                }
                
                var rowCount = 0
                while (rowIndex < monthlySchedule.length() && rowCount < rowsPerPage) {
                    val row = monthlySchedule.getJSONObject(rowIndex)
                    
                    // Alternate row background
                    if (rowCount % 2 == 1) {
                        val altBg = Paint().apply {
                            color = Color.parseColor("#f5f5f5")
                            style = Paint.Style.FILL
                        }
                        canvas.drawRect(margin, currentY, pageWidth - margin, currentY + 16f, altBg)
                    }
                    
                    // Highlight prepayment rows
                    val prepay = row.optDouble("prepay", 0.0)
                    if (prepay > 0) {
                        val prepayBg = Paint().apply {
                            color = Color.parseColor("#c8e6c9")
                            style = Paint.Style.FILL
                        }
                        canvas.drawRect(margin, currentY, pageWidth - margin, currentY + 16f, prepayBg)
                    }
                    
                    // Highlight disbursal rows
                    val disbursal = row.optDouble("disbursal", 0.0)
                    if (disbursal > 0) {
                        val disbursalBg = Paint().apply {
                            color = Color.parseColor("#fff9c4")
                            style = Paint.Style.FILL
                        }
                        canvas.drawRect(margin, currentY, pageWidth - margin, currentY + 16f, disbursalBg)
                    }
                    
                    colX = margin + 5f
                    val values = arrayOf(
                        row.optInt("month_number", 0).toString(),
                        row.optString("month_name", ""),
                        formatRupees(row.optDouble("opening", 0.0)),
                        formatRupees(row.optDouble("interest", 0.0)),
                        if (disbursal > 0) formatRupees(disbursal) else "-",
                        if (row.optDouble("emi", 0.0) > 0) formatRupees(row.optDouble("emi", 0.0)) else "-",
                        if (prepay > 0) formatRupees(prepay) else "-",
                        formatRupees(row.optDouble("closing", 0.0))
                    )
                    
                    for (i in values.indices) {
                        canvas.drawText(values[i], colX, currentY + 12f, tableTextPaint)
                        colX += colWidths[i]
                    }
                    
                    currentY += 16f
                    rowIndex++
                    rowCount++
                }
                
                // Page number
                canvas.drawText("Page $pageNumber", pageWidth / 2f - 20f, pageHeight - 20f, smallTextPaint)
                
                document.finishPage(page)
            }
        }
        
        // Save PDF
        val downloadsDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS)
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val file = File(downloadsDir, "Loan_Payoff_Plan_$timestamp.pdf")
        
        FileOutputStream(file).use { output ->
            document.writeTo(output)
        }
        
        document.close()
        
        return file
    }
}
