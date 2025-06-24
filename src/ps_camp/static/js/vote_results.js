async function fetchVotes() {
  try {
    const res = await fetch("/api/live_votes");
    const data = await res.json();

    // 更新時間
    const timestamp = new Date(data.timestamp);
    document.getElementById("timestamp").textContent = timestamp.toLocaleString();

    const partyVotes = data.votes.party_votes || {};
    const partyNames = data.votes.party_names || {};
    const totalPartyVotes = Object.values(partyVotes).reduce((a, b) => a + b, 0);

    // ===== 渲染政黨票橫幅 =====
    const partyContainer = document.getElementById("party-bars");
    partyContainer.innerHTML = "";

    for (const [partyId, count] of Object.entries(partyVotes)) {
      const name = partyNames[partyId] || partyId;
      const percent = totalPartyVotes > 0 ? ((count / totalPartyVotes) * 100).toFixed(2) : "0.00";

      const countStr = count.toString().padStart(5, "0");
      const tenThousands = countStr.slice(0, -4) || "0";
      const remainder = countStr.slice(-4);

      const div = document.createElement("div");
      div.className = "party-bar";

      div.innerHTML = `
        <div class="party-name">${name}</div>
        <div class="party-data">
          <div class="party-percent">${percent}%</div>
          <div class="party-count">
            <span class="tenK">${tenThousands}萬</span>
            <span class="units">${remainder}</span>
          </div>
        </div>
        <div class="party-seats">席次比例：--</div>
      `;

      partyContainer.appendChild(div);
    }

    // ===== 渲染公投票橫幅 =====
    const refVotes = data.votes.referendum_votes || {};
    const totalRefVotes = (refVotes.yes || 0) + (refVotes.no || 0);

    const refContainer = document.getElementById("referendum-bars");
    refContainer.innerHTML = "";

    const types = [
      { key: "yes", label: "同意", color: "agree" },
      { key: "no", label: "不同意", color: "disagree" }
    ];

    types.forEach(({ key, label, color }) => {
      const count = refVotes[key] || 0;
      const percent = totalRefVotes > 0 ? ((count / totalRefVotes) * 100).toFixed(2) : "0.00";
      const countStr = count.toString().padStart(5, "0");
      const tenThousands = countStr.slice(0, -4) || "0";
      const remainder = countStr.slice(-4);

      const div = document.createElement("div");
      div.className = `party-bar ${color}`;

      div.innerHTML = `
        <div class="party-name">${label}</div>
        <div class="party-data">
          <div class="party-percent">${percent}%</div>
          <div class="party-count">
            <span class="tenK">${tenThousands}萬</span>
            <span class="units">${remainder}</span>
          </div>
        </div>
        <div class="party-seats">是否通過：--</div>
      `;

      refContainer.appendChild(div);
    });

  } catch (err) {
    console.error("票數抓取失敗：", err);
    document.getElementById("timestamp").textContent = "更新失敗";
  }
}

setInterval(fetchVotes, 5000);
fetchVotes();
