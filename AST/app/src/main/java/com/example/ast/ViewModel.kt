import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.ast.AddWalletRequest
import com.example.ast.DashboardResponse
import com.example.ast.ToggleRequest
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

    suspend fun updateWallet(
        userId: String,
        publicKey: String?,  // Исправлен порядок параметров
        privateKey: String?,
        positionSize: Int,
        slippageTolerance: Int,
        callback: (Boolean, String?) -> Unit  // Добавлен параметр для ошибки
    ) {
        if ((publicKey != null && privateKey == null) ||
            (publicKey == null && privateKey != null)) {
            callback(false, "Both keys must be provided together")
            return
        }

        val request = AddWalletRequest(
            userId = userId,
            publicKey = publicKey,
            privateKey = privateKey,
            positionSize = positionSize,
            slippageTolerance = slippageTolerance
        )

        networkService.addWallet(request) { success, errorMessage ->
            callback(success, errorMessage)
        }
    }

    fun toggleBot(
        userId: String,
        publicKey: String,
        isActive: Boolean,
        callback: (Boolean, String?) -> Unit
    ) {
        viewModelScope.launch {
            val request = ToggleRequest(userId, publicKey, isActive)
            networkService.toggleBot(request) { success, errorMessage ->
                callback(success, errorMessage)
            }
        }
    }
}