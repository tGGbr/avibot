#!/bin/bash

export $(cat avibot.env | xargs)
export $(cat postgres.env | xargs)
