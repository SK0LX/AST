import requests
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solders.commitment_config import CommitmentLevel
from solders.rpc.requests import SendVersionedTransaction
from solders.rpc.config import RpcSendTransactionConfig

def trade_token(keypair, mint: str, amount: int, sell: bool = True, slippage: int = 2, priority_fee: float = 0.00, pool: str = "auto") -> str:
    """
    Универсальная функция для покупки/продажи токенов на Solana.
    
    Args:
        mint (str): Адрес контракта токена
        amount (int): Количество токенов для торговли
        sell (bool): True для продажи, False для покупки
        public_key (str): Публичный ключ кошелька
        slippage (int): Процент проскальзывания
        priority_fee (float): Приоритетная комиссия
        pool (str): Биржа для торговли ("pump", "raydium", "pump-amm" или "auto")
    
    Returns:
        str: Ссылка на транзакцию в Solscan
    """
    # Формируем запрос к API
    response = requests.post(
        url="https://pumpportal.fun/api/trade-local",
        data={
            "publicKey": keypair.pubkey(),
            "action": "sell" if sell else "buy",
            "mint": mint,
            "amount": amount,
            "denominatedInSol": "false",
            "slippage": slippage,
            "priorityFee": priority_fee,
            "pool": pool
        }
    )
    
    # Проверяем успешность запроса
    if response.status_code != 200:
        raise Exception(f"API error: {response.text}")
    
    # Создаем и подписываем транзакцию
    tx = VersionedTransaction(VersionedTransaction.from_bytes(response.content).message, [keypair])
    
    # Настраиваем параметры отправки
    commitment = CommitmentLevel.Confirmed
    config = RpcSendTransactionConfig(preflight_commitment=commitment)
    
    # Отправляем транзакцию
    response = requests.post(
        url="https://api.mainnet-beta.solana.com/",
        headers={"Content-Type": "application/json"},
        data=SendVersionedTransaction(tx, config).to_json()
    )
    
    # Проверяем результат
    result = response.json()
    if 'result' not in result:
        raise Exception(f"Transaction error: {result}")
        
    tx_signature = result['result']
    return f'https://solscan.io/tx/{tx_signature}'

# Пример использования:
try:
    # Продажа 200,000 токенов
    keypair = Keypair.from_base58_string("3M6W2YqFWNUc4mJgFXbQ9LoyfHF3T5vgJJm34AykmF43GQ8jvL5BAYXeZSNVBd5CeYVBUcj54XqTYdaBsweN9gmY")

    tx_link = trade_token(
        keypair=keypair,
        mint="A5tF6BmxfBZucjNQpriLVuc2A7ui3UB9ze5sjrcqpump",
        amount=50_000,
        sell=True,
        slippage=1
    )
    print(f"Transaction: {tx_link}")
except Exception as e:
    print(f"Error: {str(e)}")