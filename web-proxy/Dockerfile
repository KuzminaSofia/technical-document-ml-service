FROM nginx:1.27-alpine

# del конфигурацию nginx
RUN rm /etc/nginx/conf.d/default.conf

# подставить свою конфигурацию
COPY nginx.conf /etc/nginx/nginx.conf