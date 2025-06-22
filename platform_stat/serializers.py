from rest_framework import serializers

class RolesSerializer(serializers.Serializer):
    new_roles_this_week = serializers.IntegerField()

class MembersSerializer(serializers.Serializer):
    total_members = serializers.IntegerField()

class CreatorsSerializer(serializers.Serializer):
    creators_looking_for_talent = serializers.IntegerField()

class SatisfiedSerializer(serializers.Serializer):
    satisfied_profiles = serializers.IntegerField()