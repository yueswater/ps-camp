bank_report_template = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <style>
    body {
      font-family: "Noto Sans TC", sans-serif;
      margin: 2rem;
      color: #111;
    }
    h1 {
      text-align: center;
      font-size: 1.8rem;
      margin-bottom: 1rem;
    }
    .balance {
      margin-bottom: 1.5rem;
      font-size: 1.1rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th, td {
      border: 1px solid #333;
      padding: 8px;
      text-align: center;
    }
    th {
      background-color: #f0f0f0;
    }
  </style>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC&display=swap" rel="stylesheet">
</head>
<body>
  <h1>銀行交易明細</h1>
  <div style="display: flex; justify-content: space-between; margin-bottom: 1rem; font-size: 0.9rem; color: #666;">
    <div>帳戶名稱：{{ account_to_fullname.get(account.id, "未知使用者") }}</div>
    <div>匯出時間：{{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}</div>
  </div>
  <p class="balance">可用餘額：<strong>NT$ {{ "{:,}".format(account.balance) }}</strong></p>

  <table>
    <thead>
      <tr>
        <th>時間</th>
        <th>類型</th>
        <th>對象</th>
        <th>金額</th>
        <th>備註</th>
      </tr>
    </thead>
    <tbody>
      {% for tx in transactions %}
      <tr>
        <td>{{ tx.created_at.strftime('%Y-%m-%d') }}</td>
        <td>
          {% if tx.from_account_id == account.id and account_to_fullname.get(tx.to_account_id) == "中央銀行" %}
            提款
          {% elif tx.to_account_id == account.id and account_to_fullname.get(tx.from_account_id) == "中央銀行" %}
            存款
          {% elif tx.from_account_id == account.id %}
            轉出
          {% else %}
            轉入
          {% endif %}
        </td>
        <td>
          {% if tx.from_account_id == account.id and account_to_fullname.get(tx.to_account_id) == "中央銀行" %}
            -
          {% elif tx.from_account_id == account.id %}
            {{ account_to_fullname.get(tx.to_account_id, "未知") }}
          {% else %}
            {{ account_to_fullname.get(tx.from_account_id, "未知") }}
          {% endif %}
        </td>
        <td>NT$ {{ "{:,}".format(-tx.amount if tx.from_account_id == account.id else tx.amount) }}</td>
        <td>{{ tx.note or "-" }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""
