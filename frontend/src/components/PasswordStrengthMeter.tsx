interface Props {
  password: string;
}

const STRENGTH_LABELS = ["", "Weak", "Fair", "Good", "Strong"];
const STRENGTH_COLORS = [
  "",
  "bg-red-500",
  "bg-orange-400",
  "bg-yellow-400",
  "bg-green-500",
];

function getStrength(password: string): 0 | 1 | 2 | 3 | 4 {
  if (!password) return 0;
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  return score as 0 | 1 | 2 | 3 | 4;
}

export default function PasswordStrengthMeter({ password }: Props) {
  const strength = getStrength(password);

  if (!password) return null;

  return (
    <div className="mt-1 space-y-1">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((level) => (
          <div
            key={level}
            className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
              strength >= level ? STRENGTH_COLORS[strength] : "bg-gray-200"
            }`}
          />
        ))}
      </div>
      <p className={`text-xs ${strength <= 1 ? "text-red-500" : strength <= 2 ? "text-yellow-500" : "text-green-600"}`}>
        {STRENGTH_LABELS[strength]}
      </p>
    </div>
  );
}
