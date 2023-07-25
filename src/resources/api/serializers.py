from datetime import datetime

from PIL import Image
from authors.models import Author
from resources.models import Resource, Keyword, Theme, Audience, Category
from rest_framework import serializers
from utilities.file import save_image_with_path


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class AudienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audience
        fields = '__all__'

class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = '__all__'

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'

class ResourceSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=False)
    audience = AudienceSerializer(many=True)
    theme = ThemeSerializer(many=True)
    authors = AuthorSerializer(many=True)
    keywords = KeywordSerializer(many=True, required=False)

    class Meta:
        model = Resource
        fields = ['id', 'name', 'url', 'abstract' , 'image1', 'image2','authors', 'audience', 'dateUploaded', 'keywords',
                'category', 'license', 'publisher', 'datePublished', 'theme', 'inLanguage', 'resourceDOI', 'featured']

class TrainingResourceSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=False)
    audience = AudienceSerializer(many=True)
    theme = ThemeSerializer(many=True)
    authors = AuthorSerializer(many=True)
    keywords = KeywordSerializer(many=True, required=False)

    class Meta:
        model = Resource
        fields = ['id', 'name', 'url', 'abstract' , 'image1', 'image2','authors', 'audience', 'dateUploaded', 'keywords',
                'category', 'license', 'publisher', 'datePublished', 'theme', 'inLanguage', 'resourceDOI', 'featured',
                'own']

class ResourceSerializerCreateUpdate(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=False)
    audience = serializers.PrimaryKeyRelatedField(queryset=Audience.objects.all(), many=True)
    theme = serializers.PrimaryKeyRelatedField(queryset=Theme.objects.all(), many=True)
    keywords = serializers.CharField(required=False)
    authors = serializers.CharField(required=True)

    class Meta:
        model = Resource
        fields = ['id', 'name', 'url', 'abstract' , 'image1', 'image2','authors', 'audience', 'keywords',
            'category', 'license', 'publisher', 'datePublished', 'theme', 'inLanguage', 'resourceDOI', 'featured']

    def validate(self, data):
        if not self.partial:
            if data['theme'] == []:
                raise serializers.ValidationError({'theme': ["This field is required."]})
            if data['audience'] == []:
                raise serializers.ValidationError({'audience': ["This field is required."]})

        return data

    def save(self, args, **kwargs):               
        keywords = self.validated_data.get('keywords')
        if(keywords):
            choices = keywords.split(',')
            for choice in choices:
                if(choice != ''):
                    keyword = Keyword.objects.get_or_create(keyword=choice)
            keywords = Keyword.objects.all()
            keywords = keywords.filter(keyword__in = choices)        
        else:
            keywords = []
        
        # Authors
        authors = self.validated_data.get('authors')
        if(authors):
            choices = authors.split(',')
            for choice in choices:
                if(choice != ''):
                    Author.objects.get_or_create(author=choice)
            authors = Author.objects.all()
            authors = authors.filter(author__in = choices)
        else:
            authors = []

        image1 = self.validated_data.get('image1')
        if(image1):
            photo = image1
            image = Image.open(photo)
            image_path = save_image_with_path(image, photo.name)
            image1 = image_path

        image2 = self.validated_data.get('image2')
        if(image2):
            photo = image2
            image = Image.open(photo)
            image_path = save_image_with_path(image, photo.name)
            image2 = image_path


        publication_date = datetime.now()

        moreItems = [('creator', args.user),('keywords', keywords), ('authors', authors), ('dateUploaded', publication_date), 
        ('image1', image1), ('image2', image2)]

        data =  dict(
            list(self.validated_data.items()) +
            list(kwargs.items()) + list(moreItems)
        )
            
        self.instance = self.create(data)

        return "success"

    def update(self, instance, validated_data, requestData):
        keywordsSent = False
        authorsSent = False
        image1Sent = False
        image2Sent = False
        if 'keywords' in requestData:
            keywords = ""
            if requestData.get('keywords'):
                keywords = validated_data.pop('keywords')
            keywordsSent = True

        if 'authors' in requestData:
            if requestData.get('authors'):
                authors = validated_data.pop('authors')
                authorsSent = True
            else:
                instance.authors  = None                           

        if 'image1' in requestData:
            if requestData.get('image1'):
                image1 = validated_data.pop('image1')
            image1Sent = True

        if 'image2' in requestData:
            if requestData.get('image2'):
                image2 = validated_data.pop('image2')
            image2Sent = True

        super().update(instance, validated_data)

        if(keywordsSent):
            choices = keywords.split(',')
            for choice in choices:
                if(choice != ''):
                    keyword = Keyword.objects.get_or_create(keyword=choice)
            keywords = Keyword.objects.all()
            keywords = keywords.filter(keyword__in = choices)
            instance.keywords.set(keywords)

        if(authorsSent):
            for choice in choices:
                if(choice != ''):
                    author, exist = Author.objects.get_or_create(author=choice)
            authors = Author.objects.all()
            authors = authors.filter(author__in = choices)
            instance.authors.set(authors)

        if(image1Sent):
            if(image1):
                photo = image1
                image = Image.open(photo)
                image_path = save_image_with_path(image, photo.name)
                instance.image1 = image_path

        if(image2Sent):
            if(image2):
                photo = image2
                image = Image.open(photo)
                image_path = save_image_with_path(image, photo.name)
                instance.image2 = image_path

        instance.save()
        return instance


class TrainingResourceSerializerCreateUpdate(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=False)
    audience = serializers.PrimaryKeyRelatedField(queryset=Audience.objects.all(), many=True)
    theme = serializers.PrimaryKeyRelatedField(queryset=Theme.objects.all(), many=True)
    keywords = serializers.CharField(required=False)
    authors = serializers.CharField(required=True)

    class Meta:
        model = Resource
        fields = ['id', 'name', 'url', 'abstract' , 'image1', 'image2','authors', 'audience', 'keywords',
                'category', 'license', 'publisher', 'datePublished', 'theme', 'inLanguage', 'resourceDOI', 'featured',
                'own']

    def validate(self, data):
        if not self.partial:
            if data['theme'] == []:
                raise serializers.ValidationError({'theme': ["This field is required."]})
            if data['audience'] == []:
                raise serializers.ValidationError({'audience': ["This field is required."]})

        return data

    def save(self, args, **kwargs):               
        keywords = self.validated_data.get('keywords')
        if(keywords):
            choices = keywords.split(',')
            for choice in choices:
                if(choice != ''):
                    keyword = Keyword.objects.get_or_create(keyword=choice)
            keywords = Keyword.objects.all()
            keywords = keywords.filter(keyword__in = choices)        
        else:
            keywords = []
        
        # Authors
        authors = self.validated_data.get('authors')
        if(authors):
            choices = authors.split(',')
            for choice in choices:
                if(choice != ''):
                    Author.objects.get_or_create(author=choice)
            authors = Author.objects.all()
            authors = authors.filter(author__in = choices)
        else:
            authors = []

        image1 = self.validated_data.get('image1')
        if(image1):
            photo = image1
            image = Image.open(photo)
            image_path = save_image_with_path(image, photo.name)
            image1 = image_path

        image2 = self.validated_data.get('image2')
        if(image2):
            photo = image2
            image = Image.open(photo)
            image_path = save_image_with_path(image, photo.name)
            image2 = image_path


        publication_date = datetime.now()

        isTrainingResource = True


        moreItems = [('creator', args.user),('keywords', keywords), ('authors', authors), ('dateUploaded', publication_date), 
        ('image1', image1), ('image2', image2), ('isTrainingResource', isTrainingResource)]

        data =  dict(
            list(self.validated_data.items()) +
            list(kwargs.items()) + list(moreItems)
        )
            
        self.instance = self.create(data)

        return "success"

    def update(self, instance, validated_data, requestData):
        keywordsSent = False
        authorsSent = False
        image1Sent = False
        image2Sent = False
        if 'keywords' in requestData:
            keywords = ""
            if requestData.get('keywords'):
                keywords = validated_data.pop('keywords')
            keywordsSent = True

        if 'authors' in requestData:
            if requestData.get('authors'):
                authors = validated_data.pop('authors')
                authorsSent = True
            else:
                instance.authors  = None                           

        if 'image1' in requestData:
            if requestData.get('image1'):
                image1 = validated_data.pop('image1')
            image1Sent = True

        if 'image2' in requestData:
            if requestData.get('image2'):
                image2 = validated_data.pop('image2')
            image2Sent = True

        super().update(instance, validated_data)

        if(keywordsSent):
            choices = keywords.split(',')
            for choice in choices:
                if(choice != ''):
                    keyword = Keyword.objects.get_or_create(keyword=choice)
            keywords = Keyword.objects.all()
            keywords = keywords.filter(keyword__in = choices)
            instance.keywords.set(keywords)

        if(authorsSent):
            for choice in choices:
                if(choice != ''):
                    author, exist = Author.objects.get_or_create(author=choice)
            authors = Author.objects.all()
            authors = authors.filter(author__in = choices)
            instance.authors.set(authors)

        if(image1Sent):
            if(image1):
                photo = image1
                image = Image.open(photo)
                image_path = save_image_with_path(image, photo.name)
                instance.image1 = image_path

        if(image2Sent):
            if(image2):
                photo = image2
                image = Image.open(photo)
                image_path = save_image_with_path(image, photo.name)
                instance.image2 = image_path

        instance.save()
        return instance
