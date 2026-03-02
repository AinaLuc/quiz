#!/bin/bash

# test_quiz.sh
# Usage: ./test_quiz.sh your@email.com "Your Name"

EMAIL=${1:-"test@example.com"}
NAME=${2:-"Test Coach"}
URL="http://localhost:5000/submit-quiz"

echo "🚀 Sending test quiz data for $NAME ($EMAIL)..."

curl -X POST $URL \
  -d "name=$NAME" \
  -d "email=$EMAIL" \
  -d "Q1=Executive Leadership Coaching" \
  -d "Q2=I naturally give advice on career transitions and managing high-stress teams." \
  -d "Q3=Intermediate (some clients)" \
  -d "Q4=Newly promoted VP-level executives in tech companies" \
  -d "Q5=I feel like I'm constantly firefighting and have no time to lead strategically." \
  -d "Q6=To gain 10 hours back per week and feel confident in my team's autonomy." \
  -d "Q7=People looking for life coaching or general wellness advice." \
  -d "Q8=Hybrid (1-on-1 + Digital assets)" \
  -d "Q9=12 weeks" \
  -d "Q10=$2,000 - $5,000" \
  -d "Q12=500 - 2,000" \
  -d "Q13=That I won't be able to deliver enough value to justify the high price point." \
  -d "Q14=15 - 30 hours" \
  -d "Q15_interest=Yes" \
  -d "Q15=\$500 - \$2,000" \
  -d "Q16=Having a baseline of 5 active high-ticket clients and a repeatable system." \
  -d "Q17=Referrals" \
  -d "Q17=LinkedIn" \
  -d "Q17_other=Workshops"

echo -e "\n\n✅ Done! Check your app logs and your email inbox."
