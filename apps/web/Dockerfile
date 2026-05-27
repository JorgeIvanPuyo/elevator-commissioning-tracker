FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY next.config.ts postcss.config.js tailwind.config.ts tsconfig.json next-env.d.ts ./
COPY src ./src
COPY public ./public

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
