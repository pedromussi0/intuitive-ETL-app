# frontend/Dockerfile

# ---- Build Stage ----
    FROM node:18-alpine AS builder
    WORKDIR /app

    ARG VITE_API_BASE_URL_ARG
    ENV VITE_API_BASE_URL=$VITE_API_BASE_URL_ARG
    
    COPY package*.json ./
    
    RUN npm install --legacy-peer-deps
    
    COPY public ./public
    COPY src ./src
    COPY index.html vite.config.js ./
    
    
    
    RUN npm run build
    
    # ---- Final Stage ----
    FROM nginx:1.25-alpine AS final
    
    RUN rm /etc/nginx/conf.d/default.conf
    
    COPY nginx.conf /etc/nginx/conf.d/default.conf
    
    COPY --from=builder /app/dist /usr/share/nginx/html
    
    EXPOSE 80