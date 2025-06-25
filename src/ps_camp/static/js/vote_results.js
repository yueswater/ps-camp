// 移除 mockData，改為從 API 獲取真實數據
let currentData = null;

function formatNumber(num) {
    if (num >= 10000) {
        const wan = Math.floor(num / 10000);
        const remainder = num % 10000;
        return {
            main: wan,
            unit: "萬",
            sub: remainder > 0 ? remainder.toString().padStart(4, "0") : "",
        };
    }
    return {
        main: num,
        unit: "",
        sub: "",
    };
}

// 從後端 API 獲取投票結果
async function fetchVoteResults() {
    try {
        const response = await fetch("/api/live_votes"); // 使用正確的 API endpoint
        if (!response.ok) {
            throw new Error("Failed to fetch vote results");
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching vote results:", error);
        // 如果 API 失敗，返回空數據結構
        return {
            timestamp: new Date().toISOString(),
            votes: {
                party_votes: {},
                party_names: {},
                referendum_votes: { yes: 0, no: 0 },
            },
        };
    }
}

async function updateResults() {
    // 獲取最新數據
    currentData = await fetchVoteResults();
    const data = currentData;

    // 更新時間戳
    const timestamp = new Date(data.timestamp);
    const timestampElement = document.getElementById("last-update");
    if (timestampElement) {
        timestampElement.textContent = timestamp.toLocaleString("zh-TW");
    }

    // 處理政黨票
    const partyVotes = data.votes.party_votes || {};
    const partyNames = data.votes.party_names || {};
    const totalPartyVotes = Object.values(partyVotes).reduce((a, b) => a + b, 0);

    // 更新統計卡片
    const totalVotesElement = document.getElementById("total-votes");
    const turnoutElement = document.getElementById("turnout");
    const leadingPartyElement = document.getElementById("leading-party");

    if (totalVotesElement) {
        totalVotesElement.textContent = totalPartyVotes.toLocaleString();
    }

    if (turnoutElement) {
        // 你可以從後端傳送真實的投票率，或者根據總投票數計算
        const estimatedTurnout = data.votes.turnout || "計算中";
        turnoutElement.textContent =
            typeof estimatedTurnout === "number"
                ? `${estimatedTurnout.toFixed(1)}%`
                : estimatedTurnout;
    }

    // 找出領先政黨
    if (leadingPartyElement && Object.keys(partyVotes).length > 0) {
        const leadingParty = Object.entries(partyVotes).reduce((a, b) =>
            a[1] > b[1] ? a : b
        );
        leadingPartyElement.textContent = partyNames[leadingParty[0]] || "計算中";
    }

    // 渲染政黨票結果 - 新的卡片式設計
    const partyContainer = document.getElementById("party-results");
    if (partyContainer) {
        partyContainer.innerHTML = "";
        partyContainer.className = "party-grid"; // 設定為網格佈局

        // 按票數排序
        const sortedParties = Object.entries(partyVotes).sort(
            ([, a], [, b]) => b - a
        );

        sortedParties.forEach(([partyId, count]) => {
            const name = partyNames[partyId] || partyId;
            const percent =
                totalPartyVotes > 0
                    ? ((count / totalPartyVotes) * 100).toFixed(1)
                    : "0.0";
            const formatted = formatNumber(count);

            const item = document.createElement("div");
            item.className = "party-card"; // 改為 party-card
            item.innerHTML = `
                <div class="party-card-header">
                    <div class="party-name">${name}</div>
                    <div class="percentage-badge">${percent}%</div>
                </div>
                <div class="vote-count">
                    <span class="count-main">${formatted.main.toLocaleString()}</span>
                    <span class="count-unit">${formatted.unit}</span>
                    ${formatted.sub
                    ? `<span class="count-sub">${formatted.sub}</span>`
                    : ""
                }
                </div>
                <div class="vote-details">
                    <div class="detail-item">
                        <span class="detail-label">得票數</span>
                        <span class="detail-value">${count.toLocaleString()}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">席次</span>
                        <span class="detail-value">${data.votes.seats && data.votes.seats[partyId]
                    ? data.votes.seats[partyId]
                    : "待計算"
                }</span>
                    </div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${percent}%"></div>
                </div>
            `;
            partyContainer.appendChild(item);
        });
    }

    // 公投票卡片顯示
    const refVotes = data.votes.referendum_votes || {};
    const refTitles = data.votes.referendum_titles || {};
    const refContainer = document.getElementById("referendum-results");

    if (refContainer) {
        refContainer.innerHTML = "";
        refContainer.className = "party-grid"; // 與政黨票一致的卡片網格

        const sortedRefs = Object.entries(refVotes).sort(([, a], [, b]) => {
            const aTotal = (a.yes || 0) + (a.no || 0);
            const bTotal = (b.yes || 0) + (b.no || 0);
            return bTotal - aTotal;
        });

        sortedRefs.forEach(([refId, voteData]) => {
            const title = refTitles[refId] || "未命名公投案";
            const yes = voteData.yes || 0;
            const no = voteData.no || 0;
            const total = yes + no;
            const yesPercent = total > 0 ? ((yes / total) * 100).toFixed(1) : "0.0";

            const formatted = formatNumber(yes); // 只以同意票為主顯示數字

            const item = document.createElement("div");
            item.className = "party-card"; // 與政黨票卡片一致的樣式
            item.innerHTML = `
            <div class="party-card-header">
                <div class="party-name">${title}</div>
                <div class="percentage-badge">${yesPercent}%</div>
            </div>
            <div class="vote-count">
                <span class="count-main">${formatted.main.toLocaleString()}</span>
                <span class="count-unit">${formatted.unit}</span>
                ${formatted.sub
                    ? `<span class="count-sub">${formatted.sub}</span>`
                    : ""
                }
            </div>
            <div class="vote-details">
                <div class="detail-item">
                    <span class="detail-label">同意票</span>
                    <span class="detail-value">${yes.toLocaleString()}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">不同意</span>
                    <span class="detail-value">${no.toLocaleString()}</span>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${yesPercent}%"></div>
            </div>
        `;
            refContainer.appendChild(item);
        });
    }
}

// 初始化
document.addEventListener("DOMContentLoaded", function () {
    updateResults();
    // 每 5 秒更新一次數據
    setInterval(updateResults, 5000);
});

// 如果需要手動刷新功能
function refreshResults() {
    updateResults();
}
