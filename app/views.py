from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db import close_old_connections
from django.db import connection

from fcm_django.models import FCMDevice

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatRoom, Messages, Alert, User
from .serializers import (
    ChatRoomSerializer,
    AlertSerializer,
    UserLoginSerializer,
    UserSignupSerializer,
    MessageSerializer,
)


# Signe up a new user View
class UserSignupView(APIView):
    permission_classes = (AllowAny,)

    # Sigup user (create new object)
    def post(self, request):

        serializer = UserSignupSerializer(data=request.data)

        if serializer.is_valid():
            user_data = serializer.data
            User.objects.create_user(
                email=user_data["email"],
                password=user_data["password"],
                username=user_data["username"],
                phone_no=user_data["phone_no"],
                date_of_birth=user_data["date_of_birth"],
            )

            user = authenticate(
                email=user_data["email"], password=user_data["password"]
            )
            token, _ = Token.objects.get_or_create(user=user)
            user_data["id"] = user.id
            user_data["token"] = token.key

            connection.close()
            return Response(
                {"message": "User Signed up successfully", "User": user_data},
                status=status.HTTP_201_CREATED,
            )
        else:
            connection.close()
            return Response(
                {"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    # Check if user exists or not
    def get(self, request):
        email = request.query_params.get("email")
        password = request.query_params.get("password")
        print(email + "___" + password)
        user = authenticate(email=email, password=password)
        if not user:
            connection.close()
            return Response(
                {"message": "User does not exist"}, status=status.HTTP_204_NO_CONTENT
            )
        else:
            connection.close()
            return Response(
                {"message": "User Already Exists"}, status=status.HTTP_302_FOUND
            )


# View for user login
class UserLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        req_data = request.data
        user = authenticate(email=req_data["email"], password=req_data["password"])
        if not user:
            connection.close()
            return Response(
                {"message": "Invalid Details"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            token, _ = Token.objects.get_or_create(user=user)
            connection.close()
            return Response(
                {
                    "message": "User Logged In",
                    "User": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "phone_no": user.phone_no,
                        "date_of_birth": user.date_of_birth,
                        "token": token.key,
                    },
                }
            )


# Signout new user
class UserLogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user
        response = {
            "message": "User logged out",
            "Details": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "phone_no": user.phone_no,
                "date_of_birth": user.date_of_birth,
            },
        }
        request.user.auth_token.delete()
        connection.close()
        return Response(response, status=status.HTTP_200_OK)


# Register a new device to backend and store registration_id
class FCMRegisterDeviceView(APIView):
    permission_classes = (IsAuthenticated,)

    # Register a new device (create new object)
    def post(self, request):
        req_data = request.data
        user = request.user
        try:
            device = FCMDevice.objects.get(user=user)
            connection.close()
            return Response(
                {"message": "Device already registered for the user"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except:
            device = FCMDevice()
            device.device_id = req_data["device_id"]
            device.registration_id = req_data["registration_id"]
            device.type = "Android"
            device.user = request.user
            device.save()
            connection.close()
            return Response(
                {
                    "message": "New Device Registered",
                    "device_details": {
                        "device_id": device.device_id,
                        "registration_id": device.registration_id,
                        "type": device.type,
                        "user": device.user.id,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

    # Update the device_id or registraton_token for a registered device
    def patch(self, request):
        req_data = request.data
        user = request.user
        try:
            device = FCMDevice.objects.get(user=user)
            if req_data["device_id"] != None:
                device.device_id = req_data["device_id"]
            if req_data["registration_id"] != None:
                device.registration_id = req_data["registration_id"]
            device.save()
            connection.close()
            return Response(
                {
                    "message": "Device registration_id updated",
                    "device_details": {
                        "device_id": device.device_id,
                        "registration_id": device.registration_id,
                        "type": device.type,
                        "user": device.user.id,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except:
            connection.close()
            return Response(
                {"message": "User does not have a registered device"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# Send Alert notification to all the devices other than the users device
class FCMPushNotificationView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        lat = request.data["latitude"]
        lon = request.data["longitude"]
        try:
            # Checking if the user making quesry has a registered device
            user = request.user
            try:
                user_device = FCMDevice.objects.get(user=user)
            except:
                connection.close()
                return Response(
                    {"message": "The User's device is not registered"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # To get all devices other than the one who made request (only logged in users)

            tokens = Token.objects.all()
            logged_in_users = []
            for token in tokens:
                token_user = Token.objects.get(key=token).user
                if token_user != user:
                    logged_in_users.append(token_user)

            devices = FCMDevice.objects.filter(
                user__in=[user for user in logged_in_users]
            )
            # for dev in devices:
            #     print(dev.active)
            #     dev.active = True
            #     dev.save()
            #     print(dev.active)
            # print("$$$$$$$$$$$")
            # for dev in devices:
            #     print(dev.active)
            devices.send_message(
                data={
                    "lat": lat,
                    "lon": lon,
                    "user_id": user.id,
                    "user_name": user.username,
                }
            )

            # Creating a new request for help in the database
            req_ser = AlertSerializer(
                data={"user_id": user.id, "latitude": lat, "longitude": lon}
            )
            if req_ser.is_valid():
                req_ser.save()
                connection.close()
                return Response(
                    {"message": "Sent notificaion", "Request": req_ser.data},
                    status=status.HTTP_200_OK,
                )
            else:
                connection.close()
                return Response(
                    {"message": req_ser.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            connection.close()
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ViewAlert(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        today_date = datetime.today().strftime("%Y-%m-%d")
        req_objects = Alert.objects.filter(
            Q(date_time_creation__date=today_date) & ~Q(user_id=user.id)
        )
        response = AlertSerializer(req_objects, many=True)
        resp = response.data
        for req in resp:
            user_req = User.objects.get(id=req["user_id"])
            req["user_username"] = user_req.username
        connection.close()
        return Response(
            {"message": "Received Alert", "Alert": resp}, status=status.HTTP_200_OK
        )


class ViewChatRooms(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        user = request.user
        chatRooms = ChatRoom.objects.filter(
            Q(participant1_id=user.id) | Q(participant2_id=user.id)
        )
        chatRooms_serializer = ChatRoomSerializer(chatRooms, many=True)
        resp = chatRooms_serializer.data
        if len(resp) == 0:
            connection.close()
            return Response(
                {"message": "No chat rooms available"},
                status=status.HTTP_204_NO_CONTENT,
            )
        else:
            resp = chatRooms_serializer.data
            for chatroom in resp:
                user1 = User.objects.get(id=chatroom["participant1_id"])
                user2 = User.objects.get(id=chatroom["participant2_id"])
                chatroom["participant1_username"] = user1.username
                chatroom["participant2_username"] = user2.username
            connection.close()
            return Response(
                {"message": "Chat rooms found", "ChatRooms": resp},
                status=status.HTTP_200_OK,
            )


class ViewUserDetails(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        user = request.user
        connection.close()
        return Response(
            {
                "message": "User Details",
                "User": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "phone_no": user.phone_no,
                    "date_of_birth": user.date_of_birth,
                },
            }
        )


class PreviousMessagesView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):

        user = request.user
        chatroom = ChatRoom.objects.filter(
            Q(participant1_id=user.id) | Q(participant2_id=user.id)
        )
        if len(chatroom) == 0:
            connection.close()
            return Response(
                {"message": "Invalid Chat Room"}, status=status.HTTP_400_BAD_REQUEST
            )
        messages = Messages.objects.filter(chat_room_id=pk)
        messages_serializer = MessageSerializer(messages, many=True)
        resp = list(messages_serializer.data)
        connection.close()
        return Response({"Messages": resp[::-1]}, status=status.HTTP_200_OK)
