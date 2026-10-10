import { useEffect, useState } from 'react';

const EMPTY_BOARD = Array.from({ length: 6 }, () => Array(7).fill(0));

function findWinningCells(board, piece) {
  const directions = [
    [0, 1],
    [1, 0],
    [1, 1],
    [1, -1],
  ];

  for (let row = 0; row < board.length; row++) {
    for (let column = 0; column < board[row].length; column++) {
      if (board[row][column] !== piece) continue;

      for (const [rowStep, columnStep] of directions) {
        const cells = Array.from({ length: 4 }, (_, offset) => [
          row + rowStep * offset,
          column + columnStep * offset,
        ]);
        if (
          cells.every(
            ([cellRow, cellColumn]) =>
              cellRow >= 0 &&
              cellRow < board.length &&
              cellColumn >= 0 &&
              cellColumn < board[row].length &&
              board[cellRow][cellColumn] === piece,
          )
        ) {
          return cells.map(([cellRow, cellColumn]) => `${cellRow}-${cellColumn}`);
        }
      }
    }
  }

  return [];
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || 'The game server could not complete that request.');
  }
  return data;
}

function PlayerBadge({ piece, label, score, active }) {
  const isGold = piece === 1;

  return (
    <div
      className={`flex min-w-0 flex-1 items-center gap-3 rounded-2xl border bg-panel/90 px-3 py-3 shadow-panel transition sm:px-4 ${
        active
          ? isGold
            ? 'border-gold/60 ring-1 ring-gold/20'
            : 'border-sky/60 ring-1 ring-sky/20'
          : 'border-white/[0.08]'
      }`}
    >
      <span
        aria-hidden="true"
        className={`h-3.5 w-3.5 shrink-0 rounded-full shadow-lg ${
          isGold ? 'bg-gold shadow-gold/30' : 'bg-sky shadow-sky/30'
        }`}
      />
      <span className="min-w-0 flex-1 truncate text-sm font-semibold text-slate-200 sm:text-base">
        {label}
      </span>
      <span className="text-xl font-black tabular-nums text-white sm:text-2xl">{score}</span>
    </div>
  );
}

function GameResultToast({ result, onDismiss }) {
  const isDraw = result.type === 'draw';
  const isPlayerOne = result.piece === 1;

  return (
    <section
      aria-label="Game result"
      className="mt-4 w-full max-w-sm animate-[slide-in_220ms_ease-out] self-end rounded-2xl border border-white/10 bg-panel/95 p-4 shadow-panel"
      role="alert"
    >
      <div className="flex items-start gap-3">
        <span
        aria-hidden="true"
        className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl text-xl ${
          isDraw
            ? 'bg-white/10 text-slate-200'
            : isPlayerOne
              ? 'bg-gold/15 text-gold'
              : 'bg-sky/15 text-sky'
        }`}
        >
        {isDraw ? '=' : '✦'}
        </span>
        <div className="min-w-0 flex-1 pt-0.5">
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">
          {isDraw ? 'Match complete' : 'Winner'}
        </p>
        <h2 className="mt-0.5 text-lg font-black leading-tight text-white">
          {isDraw ? "It's a draw!" : `${result.playerName} wins!`}
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          {isDraw ? 'No more moves left.' : `Player ${result.piece} connected four.`}
        </p>
        </div>
        <button
        aria-label="Dismiss game result"
        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-400 transition hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky"
        onClick={onDismiss}
        type="button"
        >
        <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24">
          <path d="m6 6 12 12M18 6 6 18" stroke="currentColor" strokeLinecap="round" strokeWidth="2" />
        </svg>
        </button>
      </div>
    </section>
  );
}

export default function App() {
  const [board, setBoard] = useState(EMPTY_BOARD);
  const [mode, setMode] = useState('pvai');
  const [difficulty, setDifficulty] = useState('3');
  const [currentPlayer, setCurrentPlayer] = useState(1);
  const [scores, setScores] = useState({ 1: 0, 2: 0 });
  const [gameOver, setGameOver] = useState(true);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('Starting a new game…');
  const [result, setResult] = useState(null);
  const [winningCells, setWinningCells] = useState([]);

  async function startNewGame(nextMode = mode, nextDifficulty = difficulty) {
    setBusy(true);
    setGameOver(true);
    setResult(null);
    setWinningCells([]);
    setStatus('Starting a new game…');

    try {
      const data = await postJson('/reset', {
        mode: nextMode,
        level: nextDifficulty,
      });
      setBoard(data.board);
      setCurrentPlayer(data.next_turn);
      setGameOver(false);
      setStatus(nextMode === 'pvp' ? "Player 1's turn" : 'Your turn');
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    startNewGame('pvai', '3');
  }, []);

  async function handleMove(column) {
    if (
      busy ||
      gameOver ||
      (mode === 'pvai' && currentPlayer !== 1) ||
      board[5][column] !== 0
    ) {
      return;
    }

    setBusy(true);
    if (mode === 'pvai') setStatus('AI is thinking…');

    try {
      const data = await postJson('/play', { col: column });
      setBoard(data.board);

      if (data.status === 'win') {
        const playerName = data.player === 1 ? 'Player 1' : mode === 'pvai' ? 'AI' : 'Player 2';
        setScores((previous) => ({
          ...previous,
          [data.player]: previous[data.player] + 1,
        }));
        setGameOver(true);
        setResult({ type: 'win', piece: data.player, playerName });
        setWinningCells(findWinningCells(data.board, data.player));
        setStatus('Game over');
      } else if (data.status === 'draw') {
        setGameOver(true);
        setResult({ type: 'draw' });
        setWinningCells([]);
        setStatus('Game over');
      } else {
        setCurrentPlayer(data.next_turn);
        setStatus(
          mode === 'pvp'
            ? `Player ${data.next_turn}'s turn`
            : data.next_turn === 1
              ? 'Your turn'
              : 'AI is thinking…',
        );
      }
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  function handleModeChange(event) {
    const nextMode = event.target.value;
    setMode(nextMode);
    setScores({ 1: 0, 2: 0 });
    startNewGame(nextMode, difficulty);
  }

  function handleDifficultyChange(event) {
    const nextDifficulty = event.target.value;
    setDifficulty(nextDifficulty);
    startNewGame(mode, nextDifficulty);
  }

  function handleScoreReset() {
    setScores({ 1: 0, 2: 0 });
    startNewGame();
  }

  const playerTwoLabel = mode === 'pvai' ? 'AI' : 'Player 2';
  const isHumanTurn = mode === 'pvp' || currentPlayer === 1;

  return (
    <main className="min-h-screen overflow-hidden px-4 pb-10 pt-7 text-white sm:px-6 sm:pt-10">
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-sky/[0.07] blur-3xl" />
        <div className="absolute -right-40 top-1/3 h-96 w-96 rounded-full bg-blue-500/[0.08] blur-3xl" />
      </div>

      <div className="mx-auto flex w-full max-w-3xl flex-col items-center">
        <header className="mb-7 text-center sm:mb-9">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400 sm:text-xs">
            <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-gold" />
            The classic strategy game
          </div>
          <h1 className="text-4xl font-black tracking-[-0.06em] text-white sm:text-6xl">
            CONNECT <span className="text-gold">4</span>
          </h1>
          <p className="mt-2 text-sm text-slate-400 sm:text-base">
            Make your move. Connect four. Own the board.
          </p>
        </header>

        <section
          aria-label="Game settings"
          className="mb-5 grid w-full grid-cols-2 gap-3 rounded-2xl border border-white/[0.08] bg-panel/80 p-3 shadow-panel sm:grid-cols-[1fr_1fr_auto_auto] sm:items-end sm:gap-3 sm:p-4"
        >
          <label className="flex min-w-0 flex-col gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Game mode
            <select
              className="min-h-11 w-full rounded-xl border border-white/10 bg-night px-3 text-sm font-medium normal-case tracking-normal text-white outline-none transition focus:border-sky/60 focus:ring-2 focus:ring-sky/20"
              onChange={handleModeChange}
              value={mode}
            >
              <option value="pvai">Player vs. AI</option>
              <option value="pvp">Player vs. Player</option>
            </select>
          </label>

          {mode === 'pvai' ? (
            <label className="flex min-w-0 flex-col gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              AI difficulty
              <select
                className="min-h-11 w-full rounded-xl border border-white/10 bg-night px-3 text-sm font-medium normal-case tracking-normal text-white outline-none transition focus:border-sky/60 focus:ring-2 focus:ring-sky/20"
                onChange={handleDifficultyChange}
                value={difficulty}
              >
                <option value="1">Easy</option>
                <option value="2">Medium</option>
                <option value="3">Hard (ML)</option>
              </select>
            </label>
          ) : (
            <div aria-hidden="true" className="hidden sm:block" />
          )}

          <button
            className="min-h-11 rounded-xl bg-sky px-4 text-sm font-bold text-slate-950 transition hover:bg-sky/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky disabled:cursor-wait disabled:opacity-60"
            disabled={busy}
            onClick={() => startNewGame()}
            type="button"
          >
            New game
          </button>
          <button
            className="min-h-11 rounded-xl border border-white/10 bg-white/[0.04] px-4 text-sm font-semibold text-slate-300 transition hover:border-white/20 hover:bg-white/[0.08] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky disabled:cursor-wait disabled:opacity-60"
            disabled={busy}
            onClick={handleScoreReset}
            type="button"
          >
            Reset score
          </button>
        </section>

        <div
          aria-live="polite"
          className="mb-4 flex min-h-10 items-center justify-center gap-2 text-center text-sm font-bold text-slate-200 sm:text-base"
          role="status"
        >
          {!gameOver && !busy && isHumanTurn && (
            <span
              aria-hidden="true"
              className={`h-2 w-2 rounded-full ${
                currentPlayer === 1 ? 'bg-gold' : 'bg-sky'
              }`}
            />
          )}
          {busy && (
            <span
              aria-hidden="true"
              className="h-4 w-4 animate-spin rounded-full border-2 border-sky/30 border-t-sky"
            />
          )}
          {status}
        </div>

        <section aria-label="Score" className="mb-3 flex w-full max-w-[560px] gap-2 sm:gap-3">
          <PlayerBadge
            active={!gameOver && currentPlayer === 1}
            label="Player 1"
            piece={1}
            score={scores[1]}
          />
          <PlayerBadge
            active={!gameOver && currentPlayer === 2}
            label={playerTwoLabel}
            piece={2}
            score={scores[2]}
          />
        </section>

        <section aria-label="Connect Four game board" className="w-full max-w-[560px]">
          <div className="mb-2 grid grid-cols-7 gap-1.5 px-2 sm:gap-2 sm:px-3">
            {Array.from({ length: 7 }, (_, column) => (
              <button
                aria-label={`Drop piece in column ${column + 1}`}
                className={`grid aspect-square min-h-0 place-items-center rounded-xl text-xl transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-white/70 disabled:cursor-not-allowed sm:rounded-2xl ${
                  gameOver || busy || !isHumanTurn || board[5][column] !== 0
                    ? 'text-slate-700'
                    : currentPlayer === 1
                      ? 'text-gold/60 hover:bg-gold/10 hover:text-gold active:scale-95'
                      : 'text-sky/60 hover:bg-sky/10 hover:text-sky active:scale-95'
                }`}
                disabled={gameOver || busy || !isHumanTurn || board[5][column] !== 0}
                key={column}
                onClick={() => handleMove(column)}
                type="button"
              >
                <svg aria-hidden="true" className="h-5 w-5 sm:h-6 sm:w-6" fill="none" viewBox="0 0 24 24">
                  <path
                    d="M12 4v15m0 0-6-6m6 6 6-6"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2.2"
                  />
                </svg>
              </button>
            ))}
          </div>

          <div className="board-frame rounded-[1.35rem] border border-white/15 p-2.5 shadow-[0_24px_65px_rgba(0,0,0,0.4)] sm:rounded-[1.75rem] sm:p-4">
            <div className="grid grid-cols-7 gap-1.5 sm:gap-2.5">
              {[...board].reverse().flatMap((row, displayRow) =>
                row.map((piece, column) => (
                  <div
                    aria-label={`Row ${6 - displayRow}, column ${column + 1}, ${
                      piece === 0
                        ? 'empty'
                        : `${piece === 1 ? 'Player 1' : playerTwoLabel}${
                            winningCells.includes(`${5 - displayRow}-${column}`)
                              ? ', part of the winning four'
                              : ''
                          }`
                    }`}
                    className={`grid aspect-square place-items-center rounded-full border border-black/15 shadow-[inset_0_5px_8px_rgba(0,0,0,0.45)] ${
                      piece === 1
                        ? 'bg-gradient-to-br from-[#ffda8c] via-gold to-[#ec8f26] shadow-[0_0_14px_rgba(255,189,89,0.18),inset_0_5px_8px_rgba(0,0,0,0.2)]'
                        : piece === 2
                          ? 'bg-gradient-to-br from-[#b0ecff] via-sky to-[#35aee4] shadow-[0_0_14px_rgba(102,211,255,0.18),inset_0_5px_8px_rgba(0,0,0,0.2)]'
                          : 'bg-[#0b1830]'
                    } ${
                      winningCells.includes(`${5 - displayRow}-${column}`)
                        ? `winning-piece ${piece === 1 ? 'winning-piece-gold' : 'winning-piece-sky'}`
                        : ''
                    }`}
                    key={`${displayRow}-${column}`}
                    role="img"
                  />
                )),
              )}
            </div>
          </div>
        </section>

        <p className="mt-4 text-center text-xs text-slate-500">
          {mode === 'pvai'
            ? 'Tap or click a column to drop your piece'
            : 'Take turns with a friend — tap or click a column'}
        </p>

        {result && <GameResultToast result={result} onDismiss={() => setResult(null)} />}
      </div>
    </main>
  );
}
