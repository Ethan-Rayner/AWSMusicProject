// Copyright 2012-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.

package com.amazonaws.samples;

import java.io.File;
import java.util.Iterator;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.amazonaws.auth.profile.ProfileCredentialsProvider;
import com.amazonaws.client.builder.AwsClientBuilder;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Item;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

public class MusicLoadData {

    public static void main(String[] args) throws Exception {

        AmazonDynamoDB client = AmazonDynamoDBClientBuilder.standard()
        	.withRegion(Regions.US_EAST_1)
            .withCredentials(new ProfileCredentialsProvider("default"))
            .build();

        DynamoDB dynamoDB = new DynamoDB(client);
    	
        Table table = dynamoDB.getTable("Music");

        JsonParser parser = new JsonFactory().createParser(new File("a1.json"));     
        JsonNode rootNode = new ObjectMapper().readTree(parser);
        Iterator<JsonNode> iter = rootNode.iterator();

        ArrayNode currentNode;

        while (iter.hasNext()) {
            currentNode = (ArrayNode) iter.next();
            Iterator<JsonNode> innerIter = currentNode.iterator();

            while(innerIter.hasNext()) {
                JsonNode node = innerIter.next();

                String artist = node.path("artist").asText();
                String title = node.path("title").asText();

                try {
                    table.putItem(new Item().withPrimaryKey("title", title, "artist", artist)
                            .withJSON("year",    node.path("year").toString())
                            .withJSON("web_url", node.path("web_url").toString())
                            .withJSON("img_url", node.path("img_url").toString()));
                    

                } catch (Exception e) {
                    System.err.println("Unable to add song: " + title + " " + artist);
                    System.err.println(e.getMessage());
                    break;
                }
            }
        }
        System.out.println("Completed");
        parser.close();

    }
}