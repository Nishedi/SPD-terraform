import json
import math
import boto3

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:079654732108:TemperatureAlerts"
S3_BUCKET_NAME = "sensor-status-bucket-terraform-kp-1023"
DYNAMODB_TABLE_NAME = "SensorStatusTable"
S3_KEY = "broken_sensors.json"

sns = boto3.client("sns", region_name="us-east-1")
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)
def get_db_credentials():
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId="my-database-credentials")
    secret = json.loads(response["SecretString"])
    return secret["username"], secret["password"]

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"]) if "body" in event else event
        sensor_id = body["sensor_id"]
        resistance = float(body["value"])
	username, password = get_db_credentials()
	print("✅ Sekret odczytany:", username, password)
        if resistance < 1 or resistance > 20000:
            x = mark_sensor_as_broken(sensor_id)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "VALUE OUT OF RANGE"+" "+x})
            }

        a = 1.40e-3
        b = 2.37e-4
        c = 9.90e-8

        lnR = math.log(resistance)
        temperature_kelvin = 1 / (a + b * lnR + c * (lnR ** 3))
        temperature_celsius = temperature_kelvin - 273.15

        if temperature_celsius < -273.15 or temperature_celsius > 250:
            status = "TEMPERATURE CRITICAL"
            mark_sensor_as_broken(sensor_id)
        elif temperature_celsius >= 100:
            status = "TEMPERATURE TOO HIGH"
        elif temperature_celsius >= 20:
            status = "OK"
        else:
            status = "TEMPERATURE TOO LOW"

        if temperature_celsius > 100:
            message = f"🔥 ALERT! Sensor {sensor_id} wykrył wysoką temperaturę: {temperature_celsius}°C."
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=message,
                Subject="AWS Lambda - Alert temperatury"
            )

        response = {
            "sensor_id": sensor_id,
            "temperature_celsius": round(temperature_celsius, 2),
            "status": status
        }
        
        return {
            "statusCode": 200,
            "body": json.dumps(response)
        }
    
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        mark_sensor_as_broken(sensor_id)
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
def mark_sensor_as_broken(sensor_id):
    """Oznacza sensor jako niesprawny w S3 (dopisuje do listy) i w DynamoDB"""
    try:
        try:
            response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=S3_KEY)
            body = response["Body"].read()
            sensor_list = json.loads(body)
        except s3.exceptions.NoSuchKey:
            sensor_list = []

        if sensor_id not in sensor_list:
            sensor_list.append(sensor_id)
            
            s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=S3_KEY,
                Body=json.dumps(sensor_list),
                ContentType="application/json"
            )

        
        table.put_item(
            Item={
                "sensor_id": sensor_id,
                "broken": True
            }
        )
        return "OK"
    except Exception as e:
        return str(e)
        print(f"Error updating sensor status: {str(e)}")
# def mark_sensor_as_broken(sensor_id):
#     """Oznacza sensor jako niesprawny w S3 i DynamoDB"""
#     try:
#         # Aktualizacja w S3
#         s3.put_object(
#             Bucket=S3_BUCKET_NAME,
#             Key="broken_sensors.json",
#             Body=json.dumps({"sensor_id": sensor_id})
#         )
        
#         # Aktualizacja w DynamoDB
#         table.put_item(
#             Item={
#                 "sensor_id": sensor_id,
#                 "broken": True
#             }
#         )
#     except Exception as e:
#         print(f"Error updating sensor status: {str(e)}")
