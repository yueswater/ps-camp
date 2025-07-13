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
            .slice(0, 3); // 最多顯示 3 個

        const names = leaders.map(([id]) => partyNames[id] || id);
        const count = names.length;

        // 根據數量調整字體大小 class
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
