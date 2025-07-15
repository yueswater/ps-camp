//Party logos
const partyLogos = {
    "女性權益": "/static/images/logos/女性權益.png",
    "自由主義黨": "/static/images/logos/自由民主主義政黨.png",
    "社會民主主義政黨": "/static/images/logos/社會民主主義政黨.png",
    "勞工團結聯盟": "/static/images/logos/勞工團結聯盟.png",
    "新保守主義政黨": "/static/images/logos/新保守主義政黨.png",
    "綠黨": "/static/images/logos/綠黨.png",
};

const partyColors = {
    "女性權益": "#e91e63",
    "自由主義黨": "#2196f3",
    "社會民主主義政黨": "#9c27b0",
    "勞工團結聯盟": "#f57c00",
    "新保守主義政黨": "#3f51b5",
    "綠黨": "#4caf50",
};

//Remove mockData and get real data from the API instead
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

//Get voting results from the backend API
async function fetchVoteResults() {
    try {
        const response = await fetch("/api/live_votes"); //Use the correct API endpoint
        if (!response.ok) {
            throw new Error("Failed to fetch vote results");
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching vote results:", error);
        //If the API fails, return an empty data structure
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
    //Get the latest data
    currentData = await fetchVoteResults();
    const data = currentData;

    //Update the current time
    const currentTimeElement = document.getElementById("current-time");
    const now = new Date();
    if (currentTimeElement) {
        currentTimeElement.textContent = now.toLocaleString("zh-TW");
    }

    //Last Update Time
    const timestamp = new Date(data.timestamp);
    const timestampElement = document.getElementById("last-update");
    if (timestampElement) {
        timestampElement.textContent = timestamp.toLocaleString("zh-TW");
    }

    //Handle party tickets
    const partyVotes = data.votes.party_votes || {};
    const partyNames = data.votes.party_names || {};
    const totalPartyVotes = Object.values(partyVotes).reduce((a, b) => a + b, 0);

    //Update statistics card
    const totalVotesElement = document.getElementById("total-votes");
    const turnoutElement = document.getElementById("turnout");
    const leadingPartyElement = document.getElementById("leading-party");

    if (totalVotesElement) {
        totalVotesElement.textContent = totalPartyVotes.toLocaleString();
    }

    if (turnoutElement) {
        //You can send real turnout from the backend, or calculate based on the total number of votes
        const estimatedTurnout = data.votes.turnout;
        turnoutElement.textContent =
            typeof estimatedTurnout === "number" && !isNaN(estimatedTurnout)
                ? `${estimatedTurnout.toFixed(1)}%`
                : "計算中";
    }

    //Find the leading political party
    if (leadingPartyElement && Object.keys(partyVotes).length > 0) {
        const maxVotes = Math.max(...Object.values(partyVotes));
        const leaders = Object.entries(partyVotes)
            .filter(([, count]) => count === maxVotes)
            .slice(0, 3); //Display up to 3

        const names = leaders.map(([id]) => partyNames[id] || id);
        const count = names.length;

        //Adjust the font size according to the quantity class
        leadingPartyElement.classList.remove("leading-one", "leading-two", "leading-three");
        if (count === 1) {
            leadingPartyElement.classList.add("leading-one");
        } else if (count === 2) {
            leadingPartyElement.classList.add("leading-two");
        } else {
            leadingPartyElement.classList.add("leading-three");
        }

        leadingPartyElement.innerHTML = names.join("<br>");
    }


    //Render the results of party tickets -new card design
    const partyContainer = document.getElementById("party-results");
    if (partyContainer) {
        partyContainer.innerHTML = "";
        partyContainer.className = "party-grid"; //Set as grid layout

        //Sort by votes
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
            item.className = "party-card"; //Change to party-card
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

        //Render Bar chart
        renderBarChart(partyVotes, partyNames);
    }

    //Referendum card display
    const refVotes = data.votes.referendum_votes || {};
    const refTitles = data.votes.referendum_titles || {};
    const refContainer = document.getElementById("referendum-results");

    if (refContainer) {
        refContainer.innerHTML = "";
        refContainer.className = "referendum-grid"; //Card grid consistent with party tickets

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

            const formatted = formatNumber(yes); //Show numbers only based on consent votes

            const item = document.createElement("div");
            item.className = "party-card"; //Style consistent with party ticket cards
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

//Initialization
document.addEventListener("DOMContentLoaded", function () {
    updateResults();
    //Update data every 5 seconds
    setInterval(updateResults, 5000);
});

//If manual refresh function is required
function refreshResults() {
    updateResults();
}

function renderBarChart(partyVotes, partyNames) {
    const canvas = document.getElementById("party-bar-chart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (window.partyBarChart) {
        window.partyBarChart.destroy();
    }

    const sorted = Object.entries(partyVotes).sort(([, a], [, b]) => b - a);

    const labels = [];
    const values = [];
    const logos = [];
    const colors = [];

    for (const [id, count] of sorted) {
        const name = partyNames[id] || id;
        console.log(`政黨名稱：'${name}'`, partyLogos[name]);
        labels.push(name);
        values.push(count);
        logos.push(partyLogos[name]);
        colors.push(partyColors[name] || "#d2691e");
    }

    // 動態設定 x 軸最大值（票數最大值 + 餘裕）
    const maxVotes = Math.max(...values);
    const xAxisMax = maxVotes + Math.ceil(maxVotes * 0.1); // +10% 空間

    // 預先載入黨徽圖片
    const logoImages = logos.map((src, index) => {
        const img = new Image();
        img.src = src;
        img.onload = () => {
            if (window.partyBarChart) {
                window.partyBarChart.update();
            }
        };
        img.onerror = () => {
            console.warn(`Logo image failed to load: ${src}`);
        };
        return img;
    });

    window.partyBarChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderRadius: 6,
                barThickness: 30,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        maxRotation: 0,
                        minRotation: 0,
                        // stepSize: Math.ceil(xAxisMax / 5),
                        // callback: (value) => `${value.toLocaleString()}`
                    },
                    grid: {
                        display: false
                    },
                },
                y: {
                    ticks: { display: false }
                }
            }
        },
        plugins: [
            {
                id: 'drawPartyLogosAndLabels',
                afterDatasetsDraw(chart) {
                    const { ctx } = chart;
                    const meta = chart.getDatasetMeta(0);
                    const yAxis = chart.scales.y;

                    meta.data.forEach((bar, index) => {
                        const logoImg = logoImages[index];
                        const centerY = bar.y;
                        const logoSize = 24;

                        // 確保圖片載入成功再畫
                        if (logoImg.complete && logoImg.naturalHeight !== 0) {
                            ctx.drawImage(
                                logoImg,
                                10,
                                centerY - logoSize / 2,
                                logoSize,
                                logoSize
                            );
                        }

                        // 畫票數
                        ctx.fillStyle = "#333";
                        ctx.font = "14px sans-serif";
                        ctx.textAlign = "left";
                        ctx.textBaseline = "middle";
                        ctx.fillText(`${values[index].toLocaleString()}`, bar.x + 10, centerY);
                    });
                }
            }
        ]
    });
}
