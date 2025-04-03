import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class NetWorkService {
    private val api = RetrofitClient.instance

    fun fetchText(path: String, callback: (String?) -> Unit) {
        api.getText(path).enqueue(object : Callback<String> {
            override fun onResponse(call: Call<String>, response: Response<String>) {
                callback(response.body())
            }

            override fun onFailure(call: Call<String>, t: Throwable) {
                callback(null)
            }
        })
    }
}