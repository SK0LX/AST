package com.example.ast

import com.google.gson.annotations.SerializedName
import retrofit2.Call
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

interface ApiService {
    // Авторизация+
    @POST("/auth")
    suspend fun auth(@Body request: AuthRequest): AuthResponse

    // Верификация OTP+
    @POST("/verify")
    suspend fun verify(@Body request: VerifyRequest): VerifyResponse

    // Работа с кошельком
    @POST("wallet/add")
    suspend fun addWallet(@Body request: AddWalletRequest): Response<Unit>

    // Управление ботом
    @POST("/bot/toggle")
    suspend fun toggleBot(@Body request: ToggleRequest): Response<Unit>

    @GET("/check-auth")
    fun checkAuth(@Query("userId") userId: String): Call<CheckAuthResponse>

    // Данные дашборда+
    @GET("/dashboard")
    suspend fun getDashboard(
        @Query("userId") userId: String
    ): DashboardResponse

}


// Auth.kt
data class AuthRequest(val email: String)
data class AuthResponse(val success: Boolean, val message: String)


data class VerifyRequest(val email: String, val otp: String)
data class VerifyResponse(
    @SerializedName("userId")
    val userId: String?,

    @SerializedName("message")
    val message: String? = null
)

// Wallet.kt
data class AddWalletRequest(
    @SerializedName("userId")
    val userId: String,
    @SerializedName("publicKey")
    val publicKey: String?,
    @SerializedName("privateKey")
    val privateKey: String?,
    @SerializedName("positionSize")
    val positionSize: Int,
    @SerializedName("slippageTolerance")
    val slippageTolerance: Int
)

data class ToggleRequest(
    @SerializedName("userId")
    val userId: String,
    @SerializedName("publicKey")
    val publicKey: String,
    @SerializedName("isActive")
    val isActive: Boolean
)

// Dashboard.kt
// Dashboard.kt
data class DashboardResponse(
    @SerializedName("balance")
    val balance: String,

    @SerializedName("publicKey")
    var publicKey: String,

    @SerializedName("privateKeyPreview")
    val privateKeyPreview: String,

    @SerializedName("positionSize")
    val positionSize: Int,

    @SerializedName("slippageTolerance")
    val slippageTolerance: Int,

    @SerializedName("status")
    val status: String,

    @SerializedName("successRate")
    val successRate: Float,

    @SerializedName("tradesToday")
    val tradesToday: Int,

    @SerializedName("tradesHourly")
    val tradesHourly: Int,

    @SerializedName("totalTrades")
    val totalTrades: Int,

    @SerializedName("pnl")
    val pnl: List<PnlEntry>
)

data class PnlEntry(
    @SerializedName("date")
    val date: String,  // Или использовать LocalDateTime

    @SerializedName("value")
    val value: Double
)

data class CheckAuthResponse(val authenticated: Boolean)