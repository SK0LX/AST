package com.example.ast

import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface ApiService {
    @GET("{filename}")
    fun getText(@Path("filename") filename: String): Call<String>

    @POST("/auth")
    fun sendData(@Body data: Data): Call<String>
}