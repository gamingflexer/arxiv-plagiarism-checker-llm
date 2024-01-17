ARG OPENAI_API_KEY
ARG COPY_LEAKS_API
ARG SERP_API_KEY
ARG SUPABASE_KEY
ARG SUPABASE_URL
ARG COPY_LEAKS_EMAIL_ADDRESS
ARG COPY_LEAKS_EMAIL_KEY

FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    OPENAI_API_KEY=$OPENAI_API_KEY \
    COPY_LEAKS_API=$COPY_LEAKS_API \
    SERP_API_KEY=$SERP_API_KEY \
    SUPABASE_KEY=$SUPABASE_KEY \
    SUPABASE_URL=$SUPABASE_URL \
    COPY_LEAKS_EMAIL_ADDRESS=$COPY_LEAKS_EMAIL_ADDRESS \
    COPY_LEAKS_EMAIL_KEY=$COPY_LEAKS_EMAIL_KEY


# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

ENV GRADIO_SERVER_NAME=0.0.0.0

EXPOSE 7860

CMD ["python", "src/app.py"]