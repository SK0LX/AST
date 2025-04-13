import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.ast.DashboardResponse
import kotlinx.coroutines.launch

class AuthViewModel : ViewModel() {
    private val networkService = NetworkService()
    var lastEmail: String = "" // Сохраняем email для верификации

    // Отправка email
    suspend fun sendEmail(email: String, callback: (Boolean, String) -> Unit) {
        networkService.auth(email) { response, error ->
            if (response != null) {
                lastEmail = email
                callback(true, response.message)
            } else {
                callback(false, error ?: "Неизвестная ошибка")
            }
        }
    }

    // Отправка кода
    suspend fun verifyCode(otp: String, callback: (Boolean, String?) -> Unit) {
        if (lastEmail.isEmpty()) {
            callback(false, "Сначала введите email")
            return
        }

        networkService.verify(lastEmail, otp) { response, error ->
            if (response != null) {
                callback(true, response.userId)
            } else {
                callback(false, error)
            }
        }
    }

    suspend fun loadDashboardData(userId: String, callback: (Boolean,DashboardResponse?) -> Unit) {
        viewModelScope.launch {
            networkService.getDashboard(userId){x, message ->
                if (x != null){
                    callback(true, x)
                }
                else{
                    callback(false, null)
                }

            }
        }
    }
}