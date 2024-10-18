let userScore = 0;
let computerScore = 0;

let isMuted = false;
const muteToggleButton = document.getElementById("mute-toggle");

let currentWinningStreak = 0;
let highestWinningStreak = localStorage.getItem("highestWinningStreak") || 0;

const userScore_span = document.getElementById("user-score");
const computerScore_span = document.getElementById("computer-score");
// const scoreBoard_div = document.querySelector(".score-board");
const result_p = document.querySelector(".result > p");
const rock_div = document.getElementById("r");
const paper_div = document.getElementById("p");
const scissors_div = document.getElementById("s");
const resetButton = document.getElementById("reset-button");
const themeToggleButton = document.getElementById("theme-toggle");

const settingsIcon = document.getElementById("settings-icon");
const settingsModal = document.getElementById("settings-modal");
const closeButton = document.querySelector(".close");

settingsIcon.addEventListener("click", () => {
    settingsModal.style.display = "block";
});

closeButton.addEventListener("click", () => {
    settingsModal.style.display = "none";
});

window.addEventListener("click", (event) => {
    if (event.target === settingsModal) {
        settingsModal.style.display = "none";
    }
});

muteToggleButton.addEventListener("click", () => {
    isMuted = !isMuted;
    muteToggleButton.textContent = isMuted ? "Unmute Sounds" : "Mute Sounds";
});

function playWinSound() {
    if (!isMuted) {
        const winSound = new Audio('sounds/win.mp3');
        winSound.play();
    }
}

function playLoseSound() {
    if (!isMuted) {
        const loseSound = new Audio('sounds/lose.mp3');
        loseSound.play();
    }
}

function playDrawSound() {
    if (!isMuted) {
        const drawSound = new Audio('sounds/draw.mp3');
        drawSound.playbackRate = 1.5;
        drawSound.play();
    }
}

document.getElementById("winning-streak").textContent = `Highest Winning Streak: ${highestWinningStreak}`;

function updateWinningStreak() {
    if (currentWinningStreak > highestWinningStreak) {
        highestWinningStreak = currentWinningStreak;
        localStorage.setItem("highestWinningStreak", highestWinningStreak);
        document.getElementById("winning-streak").textContent = `Highest Streak: ${highestWinningStreak}`;
    }
}

function isLocalStorageEnabled() {
    try {
        const testKey = '__test__';
        localStorage.setItem(testKey, 'test');
        localStorage.removeItem(testKey);
        return true;
    } catch (e) {
        return false;
    }
}

if (!isLocalStorageEnabled()) {
    alert("localStorage is not enabled. Please enable it for achievements to work properly.");
}

themeToggleButton.addEventListener("click", () => {
    document.body.classList.toggle("light-theme");
    themeToggleButton.textContent = document.body.classList.contains("light-theme") ? "Switch to Dark Theme" : "Switch to Light Theme";
});

function resetGame() {
    userScore = 0;
    computerScore = 0;
    currentWinningStreak = 0;

    userScore_span.innerHTML = userScore;
    computerScore_span.innerHTML = computerScore;

    resetAchievements();
}

function resetAchievements() {
    achievements.forEach(achievement => {
        const achievementKey = `achievement_${achievement.id}`;
        localStorage.removeItem(achievementKey);
    });

    const unlockedList = document.getElementById("unlocked-achievements");
    unlockedList.innerHTML = '';

    const noneItem = document.createElement('li');
    noneItem.textContent = "None";
    unlockedList.appendChild(noneItem);

    const lockedList = document.getElementById("locked-achievements");
    lockedList.innerHTML = '';
    achievements.forEach(achievement => {
        const li = document.createElement('li');
        li.textContent = achievement.title;
        li.id = `locked_${achievement.id}`;
        lockedList.appendChild(li);
    });
}

resetButton.addEventListener("click", resetGame);

function getComputerChoice() {
    const choices = ["r", "p", "s"];
    const randomNumber = Math.floor(Math.random() * 3);
    return choices[randomNumber];
}

function convertToWord(letter) {
    if (letter === "r") return "Rock";
    if (letter === "p") return "Paper";
    return "Scissors";
}

function win(userChoice, computerChoice) {
    const smallUserWord = "user".fontsize(3).sub();
    const smallCompWord = "comp".fontsize(3).sub();
    const userChoice_div = document.getElementById(userChoice);
    userScore++;
    currentWinningStreak++;
    updateWinningStreak();
    userScore_span.innerHTML = userScore;
    computerScore_span.innerHTML = computerScore;
    result_p.innerHTML = `${convertToWord(userChoice)}${smallUserWord} beats ${convertToWord(computerChoice)}${smallCompWord} You win!🔥`
    playWinSound();
    userChoice_div.classList.add("green-glow");
    setTimeout(() => userChoice_div.classList.remove("green-glow"), 300)

    checkAchievements();
}

function lose(userChoice, computerChoice) {
    const smallUserWord = "user".fontsize(3).sub();
    const smallCompWord = "comp".fontsize(3).sub();
    const userChoice_div = document.getElementById(userChoice);
    computerScore++;
    currentWinningStreak = 0;
    userScore_span.innerHTML = userScore;
    computerScore_span.innerHTML = computerScore;
    result_p.innerHTML = `${convertToWord(userChoice)}${smallUserWord} loses to ${convertToWord(computerChoice)}${smallCompWord} You lost...💩`;
    playLoseSound();
    userChoice_div.classList.add("red-glow");
    setTimeout(() => userChoice_div.classList.remove("red-glow"), 300)

    checkAchievements();
}

function draw(userChoice, computerChoice) {
    const smallUserWord = "user".fontsize(3).sub();
    const smallCompWord = "comp".fontsize(3).sub();
    const userChoice_div = document.getElementById(userChoice);
    result_p.innerHTML = `${convertToWord(userChoice)}${smallUserWord} equals ${convertToWord(computerChoice)}${smallCompWord} It's a draw!`;
    playDrawSound();
    userChoice_div.classList.add("gray-glow");
    setTimeout(() => userChoice_div.classList.remove("gray-glow"), 300)

    checkAchievements();
}

let achievements = [
    {
        id: 1,
        title: "Win 5 Games",
        condition: () => userScore >= 5,
    },
    {
        id: 2,
        title: "Win 20 Games",
        condition: () => userScore >= 20,
    },
    {
        id: 3,
        title: "3 Winning Streak",
        condition: () => currentWinningStreak >= 3,
    },
    {
        id: 4,
        title: "5 Winning Streak",
        condition: () => currentWinningStreak >= 5,
    },
    {
        id: 5,
        title: "Lose 50 Games",
        condition: () => computerScore >= 50,
    }
];

function checkAchievements() {
    achievements.forEach(achievement => {
        const achievementKey = `achievement_${achievement.id}`;
        const isUnlocked = localStorage.getItem(achievementKey) === "true";

        if (isUnlocked) {
            displayUnlockedAchievement(achievement);
        } else if (achievement.condition()) {
            unlockAchievement(achievement);
        }
    });
}

function displayUnlockedAchievement(achievement) {
    const unlockedList = document.getElementById("unlocked-achievements");

    const noneEntry = unlockedList.querySelector('li');
    if (noneEntry && noneEntry.textContent === "None") {
        noneEntry.remove();
    }

    const li = document.createElement('li');
    li.textContent = achievement.title;
    li.id = `unlocked_${achievement.id}`;

    if (!document.getElementById(li.id)) {
        unlockedList.appendChild(li);
    }

    const lockedListItem = document.querySelector(`#locked_${achievement.id}`);
    if (lockedListItem) {
        lockedListItem.remove();
    }
}

function unlockAchievement(achievement) {
    localStorage.setItem(`achievement_${achievement.id}`, true.toString());

    displayUnlockedAchievement(achievement);
    displayAchievementPopup(achievement.title);
}

function displayAchievementPopup(achievementTitle) {
    const achievementPopup = document.createElement("div");
    achievementPopup.className = "achievement-popup";
    achievementPopup.innerText = `Achievement Unlocked: ${achievementTitle}`;
    document.body.appendChild(achievementPopup);
    setTimeout(() => {
        achievementPopup.remove();
    }, 3000);
}

function game(userChoice) {
    const computerChoice = getComputerChoice();
    switch (userChoice + computerChoice) {
        case "rs":
        case "pr":
        case "sp":
            win(userChoice, computerChoice);
            break;
        case "rp":
        case "ps":
        case "sr":
            lose(userChoice, computerChoice);
            break;
        case "rr":
        case "pp":
        case "ss":
            draw(userChoice, computerChoice);
            break;
    }
}

function main() {
    rock_div.addEventListener("click", () => game("r"));
    paper_div.addEventListener("click", () => game("p"));
    scissors_div.addEventListener("click", () => game("s"));

    resetAchievements();
    checkAchievements();
}

main();
